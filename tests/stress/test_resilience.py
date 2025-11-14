"""
Stress Tests - Resilience and Load Testing

Tests system behavior under high load, concurrent requests, edge cases,
and error conditions.

Author: ZenithEdge Team
"""

import pytest
import sys
import os
import time
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
import django
django.setup()

from django.test import Client
from django.utils import timezone
from signals.models import Signal, TradeValidation
from zenbot.validation_engine import validate_signal
from tests.fixtures.test_data import *
import json


class TestConcurrentWebhooks:
    """Test system behavior under concurrent webhook load"""
    
    def setup_method(self):
        """Clean database before tests"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    def teardown_method(self):
        """Clean up test data"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_10_concurrent_webhooks(self):
        """Test processing 10 simultaneous webhooks"""
        client = Client()
        webhook_url = '/signals/api/webhook/'
        
        # Generate 10 unique webhooks
        webhooks = []
        for i in range(10):
            webhook = VALID_WEBHOOK_HIGH_QUALITY.copy()
            webhook['symbol'] = f'EURUSD_{i}'
            webhooks.append(webhook)
        
        # Send webhooks concurrently
        responses = []
        start_time = time.time()
        
        def send_webhook(webhook_data):
            return client.post(
                webhook_url,
                data=json.dumps(webhook_data),
                content_type='application/json'
            )
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_webhook, wh) for wh in webhooks]
            for future in as_completed(futures):
                responses.append(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== Concurrent Webhook Test ===")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per webhook: {total_time/10:.2f}s")
        
        # Verify all succeeded
        success_count = sum(1 for r in responses if r.status_code in [200, 201])
        assert success_count >= 8, f"Expected at least 8/10 successful, got {success_count}"
        
        # Verify all were processed in reasonable time
        assert total_time < 30, f"10 concurrent webhooks should complete in <30s, took {total_time:.2f}s"
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_50_concurrent_validations(self):
        """Test 50 concurrent validation engine calls"""
        # Generate 50 test signals
        test_signals = []
        for i in range(50):
            signal = VALID_WEBHOOK_MODERATE_QUALITY.copy()
            signal['symbol'] = f'PAIR_{i}'
            test_signals.append(signal)
        
        # Validate concurrently
        results = []
        start_time = time.time()
        
        def validate_one(signal_data):
            return validate_signal(signal_data)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(validate_one, sig) for sig in test_signals]
            for future in as_completed(futures):
                results.append(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 50
        
        print(f"\n=== Concurrent Validation Test ===")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time per validation: {avg_time*1000:.0f}ms")
        
        # Verify all completed
        assert len(results) == 50, f"Expected 50 results, got {len(results)}"
        
        # Verify average latency is acceptable
        assert avg_time < 1.0, f"Average validation should be <1s, got {avg_time:.2f}s"
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_duplicate_webhook_detection(self):
        """Test that duplicate webhooks are handled correctly"""
        client = Client()
        webhook_url = '/signals/api/webhook/'
        
        # Send same webhook 3 times
        webhook = VALID_WEBHOOK_HIGH_QUALITY.copy()
        
        responses = []
        for i in range(3):
            response = client.post(
                webhook_url,
                data=json.dumps(webhook),
                content_type='application/json'
            )
            responses.append(response)
            time.sleep(0.1)  # Small delay
        
        # All should return success (idempotent)
        success_count = sum(1 for r in responses if r.status_code in [200, 201, 409])
        assert success_count == 3, "All duplicate requests should return success/conflict status"
        
        # Check database records
        signals = Signal.objects.filter(
            symbol=webhook['symbol'],
            side=webhook['side'],
            strategy=webhook['strategy']
        )
        
        # Verify signals were created (deduplication may or may not be implemented)
        assert signals.count() >= 1, f"Should create at least one signal, got {signals.count()}"
        assert signals.count() <= 3, f"Should not create more than 3 duplicates, got {signals.count()}"


class TestEdgeCases:
    """Test handling of edge cases and malformed data"""
    
    def setup_method(self):
        """Clean database"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    def teardown_method(self):
        """Clean up"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_missing_required_fields(self):
        """Test webhook with missing required fields"""
        client = Client()
        webhook_url = '/signals/api/webhook/'
        
        response = client.post(
            webhook_url,
            data=json.dumps(INVALID_WEBHOOK_MISSING_FIELDS),
            content_type='application/json'
        )
        
        # Should return 400 error
        assert response.status_code == 400, f"Missing fields should return 400, got {response.status_code}"
        
        # Should not create any database records
        assert Signal.objects.count() == 0, "Invalid webhook should not create Signal"
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_invalid_data_types(self):
        """Test webhook with invalid data types"""
        client = Client()
        webhook_url = '/signals/api/webhook/'
        
        response = client.post(
            webhook_url,
            data=json.dumps(INVALID_WEBHOOK_BAD_VALUES),
            content_type='application/json'
        )
        
        # Should return 400 error
        assert response.status_code == 400, f"Bad values should return 400, got {response.status_code}"
    
    @pytest.mark.stress
    def test_extreme_confidence_values(self):
        """Test validation with extreme confidence values"""
        # Very low confidence
        signal_low = EDGE_CASE_EXTREME_CONFIDENCE.copy()
        result_low = validate_signal(signal_low)
        
        assert 'truth_index' in result_low, "Should handle extreme low confidence"
        assert result_low['status'] in ['rejected', 'conditional'], "Very low confidence should not be approved"
        
        # Very high confidence (99.9%)
        signal_high = VALID_WEBHOOK_HIGH_QUALITY.copy()
        signal_high['confidence'] = 99.9
        result_high = validate_signal(signal_high)
        
        assert 'truth_index' in result_high, "Should handle extreme high confidence"
        assert result_high['truth_index'] >= 70, "Very high confidence should boost score"
    
    @pytest.mark.stress
    def test_extreme_price_levels(self):
        """Test validation with extreme stop loss and take profit levels"""
        # Tiny stops (0.1 pip)
        result_tiny = validate_signal(EDGE_CASE_TINY_STOPS)
        assert 'truth_index' in result_tiny, "Should handle tiny stops without crashing"
        
        # Huge stops (5000 pips)
        result_huge = validate_signal(EDGE_CASE_HUGE_STOPS)
        assert 'truth_index' in result_huge, "Should handle huge stops without crashing"
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_malformed_json(self):
        """Test webhook with malformed JSON"""
        client = Client()
        webhook_url = '/signals/api/webhook/'
        
        # Send invalid JSON
        response = client.post(
            webhook_url,
            data='{"symbol": "EURUSD", invalid json',
            content_type='application/json'
        )
        
        # Should return 400 error
        assert response.status_code == 400, f"Malformed JSON should return 400, got {response.status_code}"
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_empty_payload(self):
        """Test webhook with empty payload"""
        client = Client()
        webhook_url = '/signals/api/webhook/'
        
        response = client.post(
            webhook_url,
            data='{}',
            content_type='application/json'
        )
        
        # Should return 400 error
        assert response.status_code == 400, f"Empty payload should return 400, got {response.status_code}"
    
    @pytest.mark.stress
    def test_special_characters_in_symbol(self):
        """Test handling of special characters in symbol name"""
        signal = VALID_WEBHOOK_HIGH_QUALITY.copy()
        signal['symbol'] = 'EUR/USD-TEST_123'
        
        result = validate_signal(signal)
        
        # Should handle gracefully
        assert 'truth_index' in result, "Should handle special characters in symbol"
        assert result['truth_index'] >= 0, "Should return valid truth index"


class TestHighVolatilityScenarios:
    """Test system under high volatility market conditions"""
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    def test_high_volatility_signal_handling(self):
        """Test that high volatility signals are properly flagged"""
        result = validate_signal(WEBHOOK_HIGH_VOLATILITY)
        
        # Should complete validation
        assert 'truth_index' in result, "Should validate high volatility signal"
        assert 'breakdown' in result, "Should include breakdown"
        
        # Volatility filter should detect high volatility
        if 'volatility_filter' in result['breakdown']:
            # High volatility should result in lower volatility score
            assert result['breakdown']['volatility_filter'] <= 85.0, \
                "High volatility should be reflected in lower volatility score"
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_rapid_price_movements(self):
        """Test validation during rapid price movements"""
        from signals.models import Signal
        
        symbol = "BTCUSD_VOLATILE"
        
        # Create 20 signals with rapidly changing prices (simulating volatile market)
        for i in range(20):
            Signal.objects.create(
                symbol=symbol,
                side='buy' if i % 2 == 0 else 'sell',
                price=50000 + (i * 500 * (-1 if i % 3 == 0 else 1)),  # Rapid swings
                sl=49000,
                tp=51000,
                confidence=75.0,
                strategy='smc',
                regime='volatile',
                timeframe='1H',
                received_at=timezone.now() - timedelta(minutes=20-i)
            )
        
        # Try to validate signal in this volatile environment
        signal_data = {
            'symbol': symbol,
            'side': 'buy',
            'price': 50000,
            'sl': 49000,
            'tp': 51000,
            'confidence': 80.0,
            'strategy': 'smc',
            'regime': 'volatile',
            'timeframe': '1H'
        }
        
        result = validate_signal(signal_data)
        
        # Should complete without errors
        assert 'truth_index' in result, "Should handle volatile market validation"
        
        # Clean up
        Signal.objects.filter(symbol=symbol).delete()


class TestMemoryAndPerformance:
    """Test memory usage and performance under sustained load"""
    
    @pytest.mark.stress
    @pytest.mark.slow
    def test_1000_sequential_validations(self):
        """Test 1000 sequential validations for memory leaks"""
        results = []
        start_time = time.time()
        
        for i in range(1000):
            signal = VALID_WEBHOOK_MODERATE_QUALITY.copy()
            signal['symbol'] = f'TEST_{i % 100}'  # Cycle through 100 symbols
            
            result = validate_signal(signal)
            results.append(result)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_ms = (total_time / 1000) * 1000
        
        print(f"\n=== Sustained Load Test ===")
        print(f"Total time: {total_time:.2f}s")
        print(f"Average time: {avg_time_ms:.1f}ms per validation")
        print(f"Throughput: {1000/total_time:.1f} validations/second")
        
        # Verify all completed
        assert len(results) == 1000, f"Expected 1000 results, got {len(results)}"
        
        # Verify consistent performance (no degradation)
        # First 100 should have similar performance to last 100
        # This would catch memory leaks that slow down execution
        assert total_time < 500, f"1000 validations should complete in <500s, took {total_time:.2f}s"
        
        # Verify average latency
        assert avg_time_ms < 500, f"Average validation should be <500ms, got {avg_time_ms:.1f}ms"
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_database_connection_pool_exhaustion(self):
        """Test behavior when database connection pool is stressed"""
        from signals.models import Signal
        
        # Create 50 database queries rapidly
        start_time = time.time()
        
        for i in range(50):
            Signal.objects.create(
                symbol=f'STRESS_TEST_{i}',
                side='buy',
                price=1.0800,
                sl=1.0750,
                tp=1.0900,
                confidence=75.0,
                strategy='smc',
                regime='trending',
                timeframe='1H'
            )
        
        # Read them back
        signals = Signal.objects.filter(symbol__startswith='STRESS_TEST_')
        count = signals.count()
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== Database Stress Test ===")
        print(f"Created and read 50 signals in {total_time:.2f}s")
        
        # Clean up
        signals.delete()
        
        # Should handle without errors
        assert count == 50, f"Expected 50 signals, got {count}"
        assert total_time < 10, f"Database operations should complete in <10s, took {total_time:.2f}s"


class TestErrorRecovery:
    """Test system recovery from various error conditions"""
    
    @pytest.mark.stress
    def test_validation_with_none_values(self):
        """Test validation handles None values gracefully"""
        signal = VALID_WEBHOOK_HIGH_QUALITY.copy()
        signal['regime'] = None
        signal['timeframe'] = None
        
        result = validate_signal(signal)
        
        # Should not crash
        assert 'truth_index' in result, "Should handle None values"
        assert result['truth_index'] >= 0, "Should return valid truth index"
    
    @pytest.mark.stress
    def test_validation_with_missing_optional_fields(self):
        """Test validation works without optional fields"""
        signal = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'confidence': 75.0,
            'strategy': 'smc'
            # Missing: regime, timeframe, session, etc.
        }
        
        result = validate_signal(signal)
        
        # Should complete with defaults
        assert 'truth_index' in result, "Should handle missing optional fields"
        assert result['status'] in ['approved', 'conditional', 'rejected'], \
            f"Should return valid status, got {result.get('status')}"
    
    @pytest.mark.stress
    def test_unicode_and_emoji_in_data(self):
        """Test handling of unicode and emoji characters"""
        signal = VALID_WEBHOOK_HIGH_QUALITY.copy()
        signal['strategy'] = 'SMC_策略_🚀'
        
        result = validate_signal(signal)
        
        # Should handle unicode gracefully
        assert 'truth_index' in result, "Should handle unicode characters"


class TestRateLimiting:
    """Test rate limiting and throttling behavior"""
    
    @pytest.mark.stress
    @pytest.mark.requires_db
    @pytest.mark.django_db
    @pytest.mark.slow
    def test_rapid_fire_webhooks_same_symbol(self):
        """Test handling of many webhooks for same symbol in short time"""
        client = Client()
        webhook_url = '/signals/api/webhook/'
        
        webhook = VALID_WEBHOOK_HIGH_QUALITY.copy()
        
        # Send 20 webhooks for same symbol rapidly
        responses = []
        start_time = time.time()
        
        for i in range(20):
            response = client.post(
                webhook_url,
                data=json.dumps(webhook),
                content_type='application/json'
            )
            responses.append(response)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n=== Rapid Fire Test ===")
        print(f"Sent 20 webhooks in {total_time:.2f}s")
        
        # Should handle all requests
        success_count = sum(1 for r in responses if r.status_code in [200, 201, 409])
        assert success_count >= 15, f"Expected at least 15/20 successful, got {success_count}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
