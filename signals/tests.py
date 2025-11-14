from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
import json

from .models import Signal


class SignalWebhookTestCase(TestCase):
    """Test cases for the signal webhook endpoint"""
    
    def setUp(self):
        self.client = Client()
        self.url = reverse('signals:signal_webhook')
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
    
    def test_valid_signal_creation(self):
        """Test that a valid signal is created and stored"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.valid_payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'received')
        self.assertIn('signal_id', data)
        
        # Verify signal was saved
        signal = Signal.objects.get(id=data['signal_id'])
        self.assertEqual(signal.symbol, 'BTCUSDT')
        self.assertEqual(signal.side, 'buy')
        self.assertEqual(signal.regime, 'Trend')
        self.assertEqual(float(signal.sl), 50000.50)
        self.assertEqual(float(signal.tp), 52000.00)
    
    def test_missing_required_field(self):
        """Test that missing required fields return error"""
        payload = self.valid_payload.copy()
        del payload['symbol']
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('symbol', data['message'])
    
    def test_invalid_side(self):
        """Test that invalid side value returns error"""
        payload = self.valid_payload.copy()
        payload['side'] = 'invalid'
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
    
    def test_invalid_regime(self):
        """Test that invalid regime value returns error"""
        payload = self.valid_payload.copy()
        payload['regime'] = 'InvalidRegime'
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
    
    def test_invalid_confidence(self):
        """Test that confidence outside 0-100 returns error"""
        payload = self.valid_payload.copy()
        payload['confidence'] = 150
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
    
    def test_invalid_json(self):
        """Test that invalid JSON returns error"""
        response = self.client.post(
            self.url,
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['status'], 'error')
        self.assertIn('Invalid JSON', data['message'])
    
    def test_sell_signal(self):
        """Test creating a sell signal"""
        payload = self.valid_payload.copy()
        payload['side'] = 'sell'
        payload['regime'] = 'Breakout'
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'received')
        
        signal = Signal.objects.get(id=data['signal_id'])
        self.assertEqual(signal.side, 'sell')
        self.assertEqual(signal.regime, 'Breakout')
    
    def test_optional_fields(self):
        """Test that optional fields can be omitted"""
        payload = self.valid_payload.copy()
        del payload['price']
        del payload['timestamp']
        
        response = self.client.post(
            self.url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        
        signal = Signal.objects.get(id=data['signal_id'])
        self.assertIsNone(signal.price)
        self.assertIsNone(signal.timestamp)
