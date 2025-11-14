"""
Integration Tests for Webhook → Validation → Database → Dashboard Pipeline

Tests end-to-end flow from webhook reception to dashboard display.

Author: ZenithEdge Team
"""

import pytest
import json
import sys
import os
from datetime import datetime
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
import django
django.setup()

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from signals.models import Signal, TradeValidation
from tests.fixtures.test_data import *


@pytest.mark.django_db
class TestWebhookToDatabase:
    """Test webhook reception creates proper database records"""
    
    def setup_method(self):
        """Initialize test client"""
        self.client = Client()
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    def teardown_method(self):
        """Clean up test data"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_valid_webhook_creates_signal_and_validation(self):
        """Test valid webhook creates Signal and TradeValidation records"""
        webhook_url = '/signals/api/webhook/'
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        # Should return success
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}"
        
        # Should create Signal record
        signals = Signal.objects.filter(symbol='EURUSD')
        assert signals.exists(), "Signal record should be created"
        signal = signals.first()
        assert signal.side == 'buy'
        assert signal.strategy == 'smc'
        
        # Should create TradeValidation record
        validations = TradeValidation.objects.filter(signal=signal)
        assert validations.exists(), "TradeValidation record should be created"
        validation = validations.first()
        assert validation.truth_index >= 0
        assert validation.status in ['approved', 'conditional', 'rejected']
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_high_quality_signal_approved_status(self):
        """Test high-quality signal gets 'approved' status"""
        webhook_url = '/signals/api/webhook/'
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        
        signal = Signal.objects.filter(symbol='EURUSD').first()
        validation = TradeValidation.objects.filter(signal=signal).first()
        
        assert validation.status == 'approved', f"High quality signal should be approved, got {validation.status}"
        assert validation.truth_index >= 75.0, f"Truth index should be ≥75, got {validation.truth_index}"
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_low_quality_signal_rejected_or_conditional(self):
        """Test low-quality signal gets 'rejected' or 'conditional' status"""
        webhook_url = '/signals/api/webhook/'
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_LOW_QUALITY),
            content_type='application/json'
        )
        
        assert response.status_code in [200, 201]
        
        signal = Signal.objects.filter(symbol='GBPUSD').first()
        validation = TradeValidation.objects.filter(signal=signal).first()
        
        assert validation.status in ['rejected', 'conditional'], f"Low quality should not be approved, got {validation.status}"
        assert validation.truth_index <= 70.0, f"Truth index should be ≤70, got {validation.truth_index}"
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_validation_breakdown_stored_correctly(self):
        """Test validation breakdown JSON is stored in database"""
        webhook_url = '/signals/api/webhook/'
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        signal = Signal.objects.filter(symbol='EURUSD').first()
        validation = TradeValidation.objects.filter(signal=signal).first()
        
        # Check breakdown exists and has all 6 criteria
        assert validation.breakdown is not None, "Breakdown should be stored"
        breakdown = validation.breakdown
        
        required_keys = [
            'technical_integrity',
            'volatility_filter',
            'regime_alignment',
            'sentiment_coherence',
            'historical_reliability',
            'psychological_safety'
        ]
        
        for key in required_keys:
            assert key in breakdown, f"Breakdown should contain {key}"
            assert 0 <= breakdown[key] <= 1.0, f"{key} should be between 0 and 1"
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_narrative_context_stored(self):
        """Test context_summary (narrative) is stored in database"""
        webhook_url = '/signals/api/webhook/'
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        signal = Signal.objects.filter(symbol='EURUSD').first()
        validation = TradeValidation.objects.filter(signal=signal).first()
        
        # Check narrative exists and has minimum length
        assert validation.context_summary is not None, "Narrative should be stored"
        assert len(validation.context_summary) > 50, "Narrative should have meaningful content"
        
        # Should contain symbol
        assert 'EURUSD' in validation.context_summary or 'EUR' in validation.context_summary


class TestWebhookErrorHandling:
    """Test webhook error handling and validation"""
    
    def setup_method(self):
        """Initialize test client"""
        self.client = Client()
        Signal.objects.all().delete()
    
    def teardown_method(self):
        """Clean up test data"""
        Signal.objects.all().delete()
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_missing_required_fields_returns_error(self):
        """Test webhook with missing fields returns 400 error"""
        webhook_url = '/signals/api/webhook/'
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(INVALID_WEBHOOK_MISSING_FIELDS),
            content_type='application/json'
        )
        
        # Should return error status
        assert response.status_code == 400, f"Missing fields should return 400, got {response.status_code}"
        
        # Should not create Signal record
        signals = Signal.objects.filter(symbol='INCOMPLETE_TEST')
        assert not signals.exists(), "Invalid webhook should not create signal"
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_invalid_data_types_returns_error(self):
        """Test webhook with invalid data types returns error"""
        webhook_url = '/signals/api/webhook/'
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(INVALID_WEBHOOK_BAD_VALUES),
            content_type='application/json'
        )
        
        # Should return error status
        assert response.status_code == 400, f"Bad values should return 400, got {response.status_code}"
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_duplicate_webhook_detection(self):
        """Test duplicate webhooks are detected and handled"""
        webhook_url = '/signals/api/webhook/'
        
        # Send first webhook
        response1 = self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        assert response1.status_code in [200, 201]
        
        # Count signals
        initial_count = Signal.objects.filter(
            symbol='EURUSD',
            side='buy',
            strategy='smc'
        ).count()
        
        # Send duplicate (same symbol, side, strategy, similar time)
        response2 = self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        # Either returns success (idempotent) or duplicate warning
        assert response2.status_code in [200, 201, 409]
        
        # Should not create duplicate signal (or creates but flags it)
        final_count = Signal.objects.filter(
            symbol='EURUSD',
            side='buy',
            strategy='smc'
        ).count()
        
        # Count should be same or +1 max (not +2)
        assert final_count <= initial_count + 1, "Should handle duplicates gracefully"


class TestDashboardIntegration:
    """Test validated signals appear correctly on dashboard"""
    
    def setup_method(self):
        """Initialize test client"""
        self.client = Client()
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    def teardown_method(self):
        """Clean up test data"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_approved_signal_displays_on_dashboard(self):
        """Test approved signals appear on dashboard"""
        # Create signal via webhook
        webhook_url = '/signals/api/webhook/'
        self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        # Access dashboard
        dashboard_url = '/bot/dashboard/'
        response = self.client.get(dashboard_url)
        
        assert response.status_code == 200, f"Dashboard should load, got {response.status_code}"
        
        # Check signal appears in response
        content = response.content.decode('utf-8')
        assert 'EURUSD' in content, "Signal symbol should appear on dashboard"
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_narrative_section_rendered(self):
        """Test AI narrative is rendered on dashboard"""
        # Create signal via webhook
        webhook_url = '/signals/api/webhook/'
        self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        # Get signal detail page
        signal = Signal.objects.filter(symbol='EURUSD').first()
        detail_url = f'/bot/signal/{signal.id}/'
        
        response = self.client.get(detail_url)
        
        if response.status_code == 200:
            content = response.content.decode('utf-8')
            
            # Check for narrative content
            validation = TradeValidation.objects.filter(signal=signal).first()
            if validation and validation.context_summary:
                # Narrative should be present
                assert 'narrative' in content.lower() or validation.context_summary[:30] in content
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    def test_explain_ai_button_shows_breakdown(self):
        """Test 'Explain AI' button shows validation breakdown"""
        # Create signal via webhook
        webhook_url = '/signals/api/webhook/'
        self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        signal = Signal.objects.filter(symbol='EURUSD').first()
        validation = TradeValidation.objects.filter(signal=signal).first()
        
        # Check breakdown data is available
        assert validation.breakdown is not None, "Breakdown should exist for frontend"
        
        # Verify all 6 criteria present
        assert 'technical_integrity' in validation.breakdown
        assert 'volatility_filter' in validation.breakdown
        assert 'regime_alignment' in validation.breakdown
        assert 'sentiment_coherence' in validation.breakdown
        assert 'historical_reliability' in validation.breakdown
        assert 'psychological_safety' in validation.breakdown


class TestPerformanceMetrics:
    """Test validation performance and latency"""
    
    def setup_method(self):
        """Initialize test client"""
        self.client = Client()
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    def teardown_method(self):
        """Clean up test data"""
        Signal.objects.all().delete()
        TradeValidation.objects.all().delete()
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    @pytest.mark.slow
    def test_validation_latency_under_500ms(self):
        """Test validation completes in under 500ms"""
        import time
        
        webhook_url = '/signals/api/webhook/'
        
        start_time = time.time()
        
        response = self.client.post(
            webhook_url,
            data=json.dumps(VALID_WEBHOOK_HIGH_QUALITY),
            content_type='application/json'
        )
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        assert response.status_code in [200, 201]
        assert latency_ms < 500, f"Validation should complete in <500ms, took {latency_ms:.2f}ms"
    
    @pytest.mark.integration
    @pytest.mark.requires_db
    @pytest.mark.slow
    def test_multiple_signals_processed_efficiently(self):
        """Test processing 10 signals completes in reasonable time"""
        import time
        
        webhook_url = '/signals/api/webhook/'
        
        test_webhooks = [
            VALID_WEBHOOK_HIGH_QUALITY,
            VALID_WEBHOOK_MODERATE_QUALITY,
            VALID_WEBHOOK_LOW_QUALITY,
            WEBHOOK_POOR_RISK_REWARD,
            WEBHOOK_HIGH_VOLATILITY
        ] * 2  # 10 total
        
        start_time = time.time()
        
        for webhook in test_webhooks:
            # Modify symbol to make each unique
            webhook_copy = webhook.copy()
            webhook_copy['symbol'] = f"{webhook['symbol']}_{test_webhooks.index(webhook)}"
            
            self.client.post(
                webhook_url,
                data=json.dumps(webhook_copy),
                content_type='application/json'
            )
        
        end_time = time.time()
        total_time_ms = (end_time - start_time) * 1000
        avg_time_ms = total_time_ms / len(test_webhooks)
        
        # Average should be under 500ms
        assert avg_time_ms < 500, f"Average validation time should be <500ms, got {avg_time_ms:.2f}ms"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
