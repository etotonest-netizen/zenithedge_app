"""
Test Fixtures for ZenithEdge AI Validation System

Provides reusable test data for all test suites:
- Webhook payloads (valid, invalid, edge cases)
- OHLCV market data samples
- News event samples
- Expected validation outputs
- Historical signal data
"""

import json
from datetime import datetime, timedelta
from decimal import Decimal


# ==========================================
# WEBHOOK PAYLOAD FIXTURES
# ==========================================

VALID_WEBHOOK_HIGH_QUALITY = {
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "buy",
    "sl": 1.0750,
    "tp": 1.0950,
    "confidence": 85.0,
    "strategy": "smc",
    "regime": "Trend",
    "price": 1.0800
}

VALID_WEBHOOK_MODERATE_QUALITY = {
    "symbol": "GBPUSD",
    "timeframe": "4H",
    "side": "sell",
    "sl": 1.2650,
    "tp": 1.2500,
    "confidence": 68.0,
    "strategy": "ict",
    "regime": "Trend",
    "price": 1.2600
}

VALID_WEBHOOK_LOW_QUALITY = {
    "symbol": "USDJPY",
    "timeframe": "15M",
    "side": "buy",
    "sl": 149.80,
    "tp": 149.95,
    "confidence": 45.0,
    "strategy": "price_action",
    "regime": "MeanReversion",
    "price": 149.90
}

INVALID_WEBHOOK_MISSING_FIELDS = {
    "symbol": "EURUSD",
    "side": "buy",
    # Missing: timeframe, sl, tp, confidence, strategy, regime
}

INVALID_WEBHOOK_BAD_VALUES = {
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "INVALID_SIDE",  # Should be 'buy' or 'sell'
    "sl": -1.0,  # Negative stop loss
    "tp": 0,  # Zero take profit
    "confidence": 150.0,  # Over 100%
    "strategy": "smc",
    "regime": "Trend",
    "price": 1.0800
}

WEBHOOK_POOR_RISK_REWARD = {
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "buy",
    "sl": 1.0750,
    "tp": 1.0820,  # Only 20 pips profit vs 50 pips risk (0.4:1 R:R)
    "confidence": 75.0,
    "strategy": "smc",
    "regime": "Trend",
    "price": 1.0800
}

WEBHOOK_HIGH_VOLATILITY = {
    "symbol": "BTCUSDT",
    "timeframe": "5M",
    "side": "buy",
    "sl": 42000,
    "tp": 45000,
    "confidence": 70.0,
    "strategy": "breakout",
    "regime": "Breakout",
    "price": 43000
}


# ==========================================
# OHLCV MARKET DATA FIXTURES
# ==========================================

def generate_ohlcv_stable(periods=100):
    """Generate stable trending OHLCV data"""
    data = []
    base_price = 1.0800
    
    for i in range(periods):
        open_price = base_price + (i * 0.0005)
        high_price = open_price + 0.0010
        low_price = open_price - 0.0005
        close_price = open_price + 0.0007
        volume = 1000 + (i * 10)
        
        data.append({
            'timestamp': datetime.now() - timedelta(hours=periods-i),
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
    
    return data


def generate_ohlcv_volatile(periods=100):
    """Generate high volatility OHLCV data"""
    data = []
    base_price = 1.0800
    
    for i in range(periods):
        import random
        volatility = random.uniform(0.0050, 0.0150)  # High volatility
        
        open_price = base_price + random.uniform(-volatility, volatility)
        high_price = open_price + volatility
        low_price = open_price - volatility
        close_price = open_price + random.uniform(-volatility/2, volatility/2)
        volume = random.randint(500, 3000)
        
        data.append({
            'timestamp': datetime.now() - timedelta(hours=periods-i),
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
        
        base_price = close_price
    
    return data


OHLCV_SAMPLE_STABLE = generate_ohlcv_stable(50)
OHLCV_SAMPLE_VOLATILE = generate_ohlcv_volatile(50)


# ==========================================
# NEWS EVENT FIXTURES
# ==========================================

NEWS_BULLISH_EUR = {
    "symbol": "EURUSD",
    "title": "ECB Raises Interest Rates by 50bps",
    "summary": "European Central Bank announces larger than expected rate hike",
    "sentiment": 0.75,  # Bullish for EUR
    "impact": 3,  # High impact
    "timestamp": datetime.now() - timedelta(hours=2)
}

NEWS_BEARISH_EUR = {
    "symbol": "EURUSD",
    "title": "Eurozone GDP Contracts 0.3%",
    "summary": "Economic data shows unexpected contraction in Q4",
    "sentiment": -0.65,  # Bearish for EUR
    "impact": 3,
    "timestamp": datetime.now() - timedelta(hours=1)
}

NEWS_NEUTRAL = {
    "symbol": "GBPUSD",
    "title": "Bank of England Holds Rates Steady",
    "summary": "Policy decision meets market expectations",
    "sentiment": 0.05,  # Neutral
    "impact": 2,
    "timestamp": datetime.now() - timedelta(hours=3)
}


# ==========================================
# EXPECTED VALIDATION OUTPUTS
# ==========================================

EXPECTED_OUTPUT_HIGH_QUALITY = {
    "truth_index_min": 80.0,
    "truth_index_max": 95.0,
    "status": "approved",
    "breakdown_requirements": {
        "technical_integrity": 0.75,  # Minimum expected
        "volatility_filter": 0.70,
        "regime_alignment": 0.75,
        "sentiment_coherence": 0.60,
        "historical_reliability": 0.65,
        "psychological_safety": 0.80
    },
    "narrative_requirements": {
        "has_header": True,
        "has_reasoning": True,
        "has_suggestion": True,
        "min_length": 100,
        "includes_risk_guidance": True
    }
}

EXPECTED_OUTPUT_LOW_QUALITY = {
    "truth_index_min": 30.0,
    "truth_index_max": 55.0,
    "status": "rejected",
    "breakdown_requirements": {
        "technical_integrity": 0.40,  # Low score expected
    },
    "should_reject": True
}


# ==========================================
# HISTORICAL SIGNAL FIXTURES
# ==========================================

HISTORICAL_SIGNALS_ONE_MONTH = [
    {
        "id": 1,
        "symbol": "EURUSD",
        "side": "buy",
        "entry": 1.0800,
        "sl": 1.0750,
        "tp": 1.0900,
        "outcome": "win",  # Hit TP
        "confidence": 85,
        "strategy": "smc",
        "timestamp": datetime.now() - timedelta(days=25)
    },
    {
        "id": 2,
        "symbol": "GBPUSD",
        "side": "sell",
        "entry": 1.2600,
        "sl": 1.2650,
        "tp": 1.2500,
        "outcome": "loss",  # Hit SL
        "confidence": 65,
        "strategy": "ict",
        "timestamp": datetime.now() - timedelta(days=24)
    },
    {
        "id": 3,
        "symbol": "EURUSD",
        "side": "buy",
        "entry": 1.0850,
        "sl": 1.0800,
        "tp": 1.0950,
        "outcome": "win",
        "confidence": 90,
        "strategy": "smc",
        "timestamp": datetime.now() - timedelta(days=23)
    },
    # Add more signals for comprehensive testing...
]


# ==========================================
# STRATEGY PERFORMANCE FIXTURES
# ==========================================

STRATEGY_PERFORMANCE_GOOD = {
    "strategy_name": "smc",
    "symbol": "EURUSD",
    "total_trades": 50,
    "winning_trades": 35,
    "losing_trades": 15,
    "win_rate": 70.0,
    "avg_win": 85.5,
    "avg_loss": 48.2,
    "expectancy": 1.45
}

STRATEGY_PERFORMANCE_POOR = {
    "strategy_name": "random_strategy",
    "symbol": "USDJPY",
    "total_trades": 20,
    "winning_trades": 7,
    "losing_trades": 13,
    "win_rate": 35.0,
    "avg_win": 45.0,
    "avg_loss": 50.0,
    "expectancy": -0.25
}

STRATEGY_PERFORMANCE_INSUFFICIENT_DATA = {
    "strategy_name": "new_strategy",
    "symbol": "GBPJPY",
    "total_trades": 5,  # Less than 10 minimum
    "winning_trades": 3,
    "losing_trades": 2,
    "win_rate": 60.0,
    "avg_win": 70.0,
    "avg_loss": 45.0,
    "expectancy": 0.48
}


# ==========================================
# RISK CONTROL FIXTURES
# ==========================================

RISK_CONTROL_NORMAL = {
    "user_id": 1,
    "daily_loss_limit": 500.0,
    "current_daily_loss": 120.0,
    "max_trades_per_day": 10,
    "current_trades_today": 3,
    "blocked": False
}

RISK_CONTROL_BREACHED = {
    "user_id": 2,
    "daily_loss_limit": 500.0,
    "current_daily_loss": 550.0,  # Over limit
    "max_trades_per_day": 10,
    "current_trades_today": 11,  # Over limit
    "blocked": True,
    "blocked_reason": "Daily loss limit exceeded"
}


# ==========================================
# CONCURRENT WEBHOOK FIXTURES (Stress Testing)
# ==========================================

def generate_concurrent_webhooks(count=100):
    """Generate multiple webhook payloads for stress testing"""
    webhooks = []
    
    for i in range(count):
        webhook = {
            "symbol": f"PAIR{i % 10}",  # Cycle through 10 pairs
            "timeframe": ["1M", "5M", "15M", "1H", "4H"][i % 5],
            "side": "buy" if i % 2 == 0 else "sell",
            "sl": 1.0000 - (0.0050 * (i % 10)),
            "tp": 1.0000 + (0.0100 * (i % 10)),
            "confidence": 50 + (i % 40),
            "strategy": ["smc", "ict", "price_action"][i % 3],
            "regime": "Trend",
            "price": 1.0000
        }
        webhooks.append(webhook)
    
    return webhooks


CONCURRENT_WEBHOOKS_100 = generate_concurrent_webhooks(100)


# ==========================================
# DUPLICATE WEBHOOK FIXTURES
# ==========================================

DUPLICATE_WEBHOOK_SET = [
    VALID_WEBHOOK_HIGH_QUALITY,
    VALID_WEBHOOK_HIGH_QUALITY,  # Exact duplicate
    VALID_WEBHOOK_HIGH_QUALITY,  # Another duplicate
]


# ==========================================
# EDGE CASE FIXTURES
# ==========================================

EDGE_CASE_EXTREME_CONFIDENCE = {
    "symbol": "EURUSD",
    "timeframe": "1H",
    "side": "buy",
    "sl": 1.0750,
    "tp": 1.0950,
    "confidence": 0.1,  # Extremely low confidence
    "strategy": "smc",
    "regime": "Trend",
    "price": 1.0800
}

EDGE_CASE_TINY_STOPS = {
    "symbol": "EURUSD",
    "timeframe": "1M",
    "side": "buy",
    "sl": 1.08000,
    "tp": 1.08001,  # 0.1 pip TP
    "confidence": 70.0,
    "strategy": "scalping",
    "regime": "Trend",
    "price": 1.08000
}

EDGE_CASE_HUGE_STOPS = {
    "symbol": "EURUSD",
    "timeframe": "1D",
    "side": "buy",
    "sl": 1.0000,
    "tp": 1.5000,  # 5000 pip move
    "confidence": 75.0,
    "strategy": "long_term",
    "regime": "Trend",
    "price": 1.0800
}


# ==========================================
# EXPORT ALL FIXTURES
# ==========================================

__all__ = [
    # Webhooks
    'VALID_WEBHOOK_HIGH_QUALITY',
    'VALID_WEBHOOK_MODERATE_QUALITY',
    'VALID_WEBHOOK_LOW_QUALITY',
    'INVALID_WEBHOOK_MISSING_FIELDS',
    'INVALID_WEBHOOK_BAD_VALUES',
    'WEBHOOK_POOR_RISK_REWARD',
    'WEBHOOK_HIGH_VOLATILITY',
    
    # OHLCV Data
    'OHLCV_SAMPLE_STABLE',
    'OHLCV_SAMPLE_VOLATILE',
    'generate_ohlcv_stable',
    'generate_ohlcv_volatile',
    
    # News Events
    'NEWS_BULLISH_EUR',
    'NEWS_BEARISH_EUR',
    'NEWS_NEUTRAL',
    
    # Expected Outputs
    'EXPECTED_OUTPUT_HIGH_QUALITY',
    'EXPECTED_OUTPUT_LOW_QUALITY',
    
    # Historical Data
    'HISTORICAL_SIGNALS_ONE_MONTH',
    
    # Strategy Performance
    'STRATEGY_PERFORMANCE_GOOD',
    'STRATEGY_PERFORMANCE_POOR',
    'STRATEGY_PERFORMANCE_INSUFFICIENT_DATA',
    
    # Risk Controls
    'RISK_CONTROL_NORMAL',
    'RISK_CONTROL_BREACHED',
    
    # Stress Testing
    'CONCURRENT_WEBHOOKS_100',
    'DUPLICATE_WEBHOOK_SET',
    'generate_concurrent_webhooks',
    
    # Edge Cases
    'EDGE_CASE_EXTREME_CONFIDENCE',
    'EDGE_CASE_TINY_STOPS',
    'EDGE_CASE_HUGE_STOPS',
]
