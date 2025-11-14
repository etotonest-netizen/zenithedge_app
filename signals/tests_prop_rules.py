from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

from .models import Signal, PropRules, check_signal_against_prop


class PropRulesTestCase(TestCase):
    """Test cases for PropRules functionality"""
    
    def setUp(self):
        self.prop_rules = PropRules.objects.create(
            name='Test Rules',
            max_daily_loss_pct=5.0,
            max_trades_per_day=5,
            max_open_positions=3,
            blackout_minutes=10,
            min_confidence_score=70.0,
            allow_weekend_trading=False,
            is_active=True,
            account_balance=Decimal('10000.00')
        )
    
    def test_confidence_check(self):
        """Test that low confidence signals are rejected"""
        signal_data = {
            'symbol': 'BTCUSDT',
            'confidence': 50.0,  # Below minimum of 70
            'side': 'buy',
            'timeframe': '1h',
            'strategy': 'ZenithEdge',
            'regime': 'Trend'
        }
        
        result = check_signal_against_prop(signal_data, self.prop_rules)
        
        self.assertFalse(result['allowed'])
        self.assertIn('Confidence', result['reason'])
    
    def test_symbol_whitelist(self):
        """Test that only whitelisted symbols are allowed"""
        self.prop_rules.allowed_symbols = 'BTCUSDT, ETHUSDT'
        self.prop_rules.save()
        
        # Allowed symbol
        result = check_signal_against_prop({
            'symbol': 'BTCUSDT',
            'confidence': 80.0,
            'side': 'buy',
            'timeframe': '1h',
            'strategy': 'ZenithEdge',
            'regime': 'Trend'
        }, self.prop_rules)
        self.assertTrue(result['allowed'])
        
        # Not allowed symbol
        result = check_signal_against_prop({
            'symbol': 'XRPUSDT',
            'confidence': 80.0,
            'side': 'buy',
            'timeframe': '1h',
            'strategy': 'ZenithEdge',
            'regime': 'Trend'
        }, self.prop_rules)
        self.assertFalse(result['allowed'])
        self.assertIn('not in allowed list', result['reason'])
    
    def test_symbol_blacklist(self):
        """Test that blacklisted symbols are rejected"""
        self.prop_rules.blacklisted_symbols = 'DOGEUSDT, SHIBUSDT'
        self.prop_rules.save()
        
        result = check_signal_against_prop({
            'symbol': 'DOGEUSDT',
            'confidence': 80.0,
            'side': 'buy',
            'timeframe': '1h',
            'strategy': 'ZenithEdge',
            'regime': 'Trend'
        }, self.prop_rules)
        
        self.assertFalse(result['allowed'])
        self.assertIn('blacklisted', result['reason'])
    
    def test_daily_trade_limit(self):
        """Test that daily trade limit is enforced"""
        # Create signals up to the limit
        for i in range(5):
            Signal.objects.create(
                symbol='BTCUSDT',
                timeframe='1h',
                side='buy',
                sl=Decimal('50000'),
                tp=Decimal('52000'),
                confidence=80.0,
                strategy='ZenithEdge',
                regime='Trend',
                is_allowed=True,
                prop_rule_checked=self.prop_rules
            )
        
        # Try one more signal
        result = check_signal_against_prop({
            'symbol': 'ETHUSDT',
            'confidence': 80.0,
            'side': 'buy',
            'timeframe': '1h',
            'strategy': 'ZenithEdge',
            'regime': 'Trend'
        }, self.prop_rules)
        
        self.assertFalse(result['allowed'])
        self.assertIn('Daily trade limit', result['reason'])
    
    def test_blackout_period(self):
        """Test that blackout period between same symbol trades is enforced"""
        # Create a recent signal for BTCUSDT
        Signal.objects.create(
            symbol='BTCUSDT',
            timeframe='1h',
            side='buy',
            sl=Decimal('50000'),
            tp=Decimal('52000'),
            confidence=80.0,
            strategy='ZenithEdge',
            regime='Trend',
            is_allowed=True,
            prop_rule_checked=self.prop_rules
        )
        
        # Try another signal for same symbol
        result = check_signal_against_prop({
            'symbol': 'BTCUSDT',
            'confidence': 80.0,
            'side': 'buy',
            'timeframe': '1h',
            'strategy': 'ZenithEdge',
            'regime': 'Trend'
        }, self.prop_rules)
        
        self.assertFalse(result['allowed'])
        self.assertIn('Blackout period', result['reason'])


class SignalWebhookWithPropRulesTestCase(TestCase):
    """Test cases for webhook with prop rules integration"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('signals:signal_webhook')
        self.prop_rules = PropRules.objects.create(
            name='Test Rules',
            max_daily_loss_pct=5.0,
            max_trades_per_day=10,
            max_open_positions=5,
            blackout_minutes=5,
            min_confidence_score=60.0,
            allow_weekend_trading=True,
            is_active=True
        )
        
        self.valid_payload = {
            "symbol": "BTCUSDT",
            "timeframe": "1h",
            "side": "buy",
            "sl": 50000.50,
            "tp": 52000.00,
            "confidence": 85.5,
            "strategy": "ZenithEdge",
            "regime": "Trend",
            "price": 51000.00,
            "timestamp": "2025-11-09T10:30:00Z"
        }
    
    def test_signal_passes_prop_rules(self):
        """Test that valid signal passes prop rules"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'received')
        self.assertTrue(data['allowed'])
        
        signal = Signal.objects.get(id=data['signal_id'])
        self.assertTrue(signal.is_allowed)
        self.assertEqual(signal.prop_rule_checked, self.prop_rules)
    
    def test_signal_fails_confidence_check(self):
        """Test that low confidence signal is rejected"""
        payload = self.valid_payload.copy()
        payload['confidence'] = 45.0  # Below minimum of 60
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'received')
        self.assertFalse(data['allowed'])
        
        signal = Signal.objects.get(id=data['signal_id'])
        self.assertFalse(signal.is_allowed)
        self.assertIn('Confidence', signal.rejection_reason)
    
    def test_no_active_prop_rules(self):
        """Test that signals are allowed when no active prop rules exist"""
        self.prop_rules.is_active = False
        self.prop_rules.save()
        
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['allowed'])
        self.assertIn('No active prop rules', data['reason'])
