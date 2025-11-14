"""
Strategy Knowledge Domains Configuration
Defines the 10 core trading strategy pillars and their cognitive layers
"""

# 10 Core Strategy Domains with Learning Targets
STRATEGY_DOMAINS = {
    'smc': {
        'name': 'Smart Money Concepts',
        'aliases': ['SMC', 'smart money', 'institutional trading'],
        'core_concepts': [
            'order block', 'fair value gap', 'FVG', 'imbalance',
            'liquidity sweep', 'break of structure', 'BOS', 'CHoCH',
            'premium zone', 'discount zone', 'optimal trade entry',
            'inducement', 'mitigation block', 'breaker block'
        ],
        'key_patterns': [
            'sweep and retest', 'FVG fill', 'displacement',
            'liquidity grab', 'turtle soup pattern'
        ],
        'psychology': 'Understanding institutional order flow and stop hunting behavior',
        'risk_context': 'Requires patience for clean setups, avoid FOMO entries',
        'visual_markers': [
            'Strong candle rejection from zone',
            'Rapid price displacement creating gaps',
            'Multiple touches creating liquidity pools'
        ]
    },
    
    'ict': {
        'name': 'Inner Circle Trader',
        'aliases': ['ICT', 'Michael Huddleston method'],
        'core_concepts': [
            'optimal trade entry', 'OTE', 'kill zone', 'power of 3',
            'judas swing', 'silver bullet', 'London session',
            'New York session', 'Asian range', 'ICT breaker',
            'balanced price range', 'liquidity void', 'turtle soup'
        ],
        'key_patterns': [
            'London reversal after Asian sweep',
            'New York manipulation',
            'Session alignment trades'
        ],
        'psychology': 'Timing based on institutional session activity',
        'risk_context': 'High win rate but requires strict session discipline',
        'visual_markers': [
            'Time-based setups at specific hours',
            'Swing highs/lows taken as liquidity',
            '50% Fibonacci retracement zones'
        ]
    },
    
    'trend': {
        'name': 'Trend-Following Systems',
        'aliases': ['trend trading', 'momentum', 'directional trading'],
        'core_concepts': [
            'higher high', 'higher low', 'trend continuation',
            'moving average', 'EMA', 'SMA', 'MACD',
            'trend line', 'channel', 'parabolic SAR',
            'ADX', 'supertrend', 'ichimoku cloud'
        ],
        'key_patterns': [
            'pullback to moving average',
            'channel breakout',
            'flag pattern continuation'
        ],
        'psychology': 'Patience to ride trends, cut losses on reversals',
        'risk_context': 'Risk trailing stop too tight in volatile trends',
        'visual_markers': [
            'Consistent series of HH/HL or LL/LH',
            'Price respecting MA as dynamic support',
            'ADX above 25 indicating strength'
        ]
    },
    
    'breakout': {
        'name': 'Breakout Strategies',
        'aliases': ['breakout trading', 'range breakout', 'volatility expansion'],
        'core_concepts': [
            'consolidation', 'range', 'triangle', 'wedge',
            'flag', 'pennant', 'coil', 'squeeze',
            'resistance breakout', 'support breakdown',
            'volume expansion', 'false breakout', 'fakeout'
        ],
        'key_patterns': [
            'tight range before earnings/news',
            'triangle apex breakout',
            'volume confirmation on break'
        ],
        'psychology': 'Fear of missing move vs false break discipline',
        'risk_context': 'High failure rate without volume confirmation',
        'visual_markers': [
            'Narrowing price range with decreasing volume',
            'Sharp move with volume spike on break',
            'Retest of broken level as support/resistance'
        ]
    },
    
    'mean_reversion': {
        'name': 'Mean Reversion Models',
        'aliases': ['reversion to mean', 'oversold bounce', 'overbought fade'],
        'core_concepts': [
            'RSI', 'stochastic', 'bollinger bands',
            'overbought', 'oversold', 'standard deviation',
            'Z-score', 'regression to mean', 'equilibrium',
            'value area', 'fair value', 'pivot point'
        ],
        'key_patterns': [
            'RSI divergence at extremes',
            'Bollinger Band squeeze and expansion',
            'Touch of outer band with reversal candle'
        ],
        'psychology': 'Contrarian mindset, buying fear and selling greed',
        'risk_context': 'Can fail in strong trending markets',
        'visual_markers': [
            'RSI below 30 or above 70',
            'Price 2+ standard deviations from mean',
            'Candlestick reversal patterns at extremes'
        ]
    },
    
    'squeeze': {
        'name': 'Squeeze Volatility Setups',
        'aliases': ['TTM squeeze', 'volatility compression', 'Keltner squeeze'],
        'core_concepts': [
            'Bollinger Bands', 'Keltner Channels', 'ATR',
            'volatility contraction', 'volatility expansion',
            'squeeze dots', 'momentum histogram',
            'breakout direction', 'compression zone'
        ],
        'key_patterns': [
            'Red squeeze dots turning gray then green',
            'Momentum histogram changing color',
            'Bands inside Keltner Channels'
        ],
        'psychology': 'Patience during consolidation, aggression on release',
        'risk_context': 'Direction uncertain until breakout confirmed',
        'visual_markers': [
            'Bollinger Bands narrowing dramatically',
            'Low ATR readings',
            'Histogram bars minimal before expansion'
        ]
    },
    
    'scalping': {
        'name': 'Scalping / Momentum Trading',
        'aliases': ['scalp', 'M1-M5 trading', 'quick in out', 'tape reading'],
        'core_concepts': [
            'order flow', 'DOM', 'tape', 'Level 2',
            'bid-ask spread', 'momentum candle', 'scalp target',
            'quick take profit', 'tight stop', 'market microstructure',
            'time and sales', 'volume profile', 'delta'
        ],
        'key_patterns': [
            'Large order absorption on DOM',
            'Volume spike with momentum candle',
            'Immediate follow-through after entry'
        ],
        'psychology': 'High focus, quick decisions, emotional control',
        'risk_context': 'Spread and commission costs eat profits',
        'visual_markers': [
            '1-5 minute candles',
            'Sharp price moves with volume',
            'Quick 5-15 pip targets'
        ]
    },
    
    'vwap': {
        'name': 'VWAP Reclaim Systems',
        'aliases': ['VWAP', 'volume weighted average price', 'anchored VWAP'],
        'core_concepts': [
            'VWAP', 'anchored VWAP', 'VWAP bands',
            'standard deviation bands', 'reclaim', 'rejection',
            'institutional reference', 'fair value line',
            'volume profile', 'value area high', 'value area low'
        ],
        'key_patterns': [
            'Price reclaims VWAP from below with volume',
            'Rejection at upper standard deviation',
            'Intraday reversion to VWAP'
        ],
        'psychology': 'Institutions use VWAP for execution benchmarks',
        'risk_context': 'Works best in liquid markets with consistent volume',
        'visual_markers': [
            'VWAP line as dynamic support/resistance',
            'Volume increase on VWAP interactions',
            'Standard deviation bands showing volatility'
        ]
    },
    
    'supply_demand': {
        'name': 'Supply & Demand Zone Analysis',
        'aliases': ['S&D', 'supply demand', 'zone trading', 'accumulation distribution'],
        'core_concepts': [
            'supply zone', 'demand zone', 'fresh zone',
            'base', 'rally', 'drop', 'RBD', 'DBR',
            'zone strength', 'time at level', 'multiple touches',
            'flip zone', 'distal line', 'proximal line'
        ],
        'key_patterns': [
            'Rally-Base-Drop for supply',
            'Drop-Base-Rally for demand',
            'Strong rejection from fresh zones'
        ],
        'psychology': 'Where was the last institutional decision made',
        'risk_context': 'Old zones lose strength after multiple touches',
        'visual_markers': [
            'Consolidation before explosive move',
            'Strong candle out of base',
            'Clean rejection on retest'
        ]
    },
    
    'confluence': {
        'name': 'Multi-Timeframe Confluence',
        'aliases': ['MTF', 'multi-timeframe', 'top-down analysis'],
        'core_concepts': [
            'higher timeframe', 'HTF', 'lower timeframe', 'LTF',
            'direction alignment', 'structure alignment',
            'confluence zone', 'triple confluence',
            'HTF support', 'LTF entry', 'timeframe agreement'
        ],
        'key_patterns': [
            'HTF trend + MTF structure + LTF pattern',
            'Weekly support + Daily demand + 4H OB',
            'Multiple timeframe MAs aligning'
        ],
        'psychology': 'Increased confidence with multi-timeframe agreement',
        'risk_context': 'Can lead to analysis paralysis',
        'visual_markers': [
            'All timeframes showing same bias',
            'Key levels aligning across timeframes',
            'Pattern confirmation on execution timeframe'
        ]
    }
}

# Strategy Interrelationships (for clustering and cross-strategy reasoning)
STRATEGY_RELATIONSHIPS = {
    'smc': ['ict', 'supply_demand', 'breakout'],
    'ict': ['smc', 'confluence', 'scalping'],
    'trend': ['confluence', 'breakout', 'vwap'],
    'breakout': ['squeeze', 'trend', 'smc'],
    'mean_reversion': ['vwap', 'supply_demand'],
    'squeeze': ['breakout', 'trend'],
    'scalping': ['ict', 'vwap', 'supply_demand'],
    'vwap': ['mean_reversion', 'scalping'],
    'supply_demand': ['smc', 'mean_reversion'],
    'confluence': ['all']  # Confluence connects to all strategies
}

# Search keywords for each strategy (for scraping and classification)
STRATEGY_KEYWORDS = {
    'smc': [
        'smart money', 'institutional', 'order block', 'fair value gap',
        'liquidity sweep', 'break of structure', 'market structure',
        'premium discount', 'OB', 'FVG', 'BOS', 'CHoCH'
    ],
    'ict': [
        'ICT', 'inner circle', 'kill zone', 'OTE', 'silver bullet',
        'judas swing', 'London', 'New York', 'Asian session',
        'optimal trade entry', 'turtle soup'
    ],
    'trend': [
        'trend following', 'momentum', 'moving average', 'EMA', 'SMA',
        'trend line', 'higher high', 'higher low', 'MACD', 'ADX',
        'directional', 'trending market'
    ],
    'breakout': [
        'breakout', 'range', 'consolidation', 'triangle', 'wedge',
        'flag', 'pennant', 'resistance break', 'support break',
        'volatility expansion', 'squeeze release'
    ],
    'mean_reversion': [
        'mean reversion', 'oversold', 'overbought', 'RSI', 'stochastic',
        'Bollinger Bands', 'reversion', 'equilibrium', 'fair value',
        'regression', 'Z-score'
    ],
    'squeeze': [
        'squeeze', 'TTM', 'volatility compression', 'Keltner',
        'Bollinger', 'consolidation', 'coil', 'tight range'
    ],
    'scalping': [
        'scalping', 'scalp', 'M1', 'M5', 'tick', 'order flow',
        'DOM', 'tape', 'Level 2', 'quick trade', 'momentum'
    ],
    'vwap': [
        'VWAP', 'volume weighted', 'anchored VWAP', 'value area',
        'volume profile', 'POC', 'point of control'
    ],
    'supply_demand': [
        'supply demand', 'supply zone', 'demand zone', 'RBD', 'DBR',
        'base', 'accumulation', 'distribution', 'zone trading'
    ],
    'confluence': [
        'confluence', 'multi-timeframe', 'MTF', 'top-down',
        'higher timeframe', 'timeframe alignment', 'HTF', 'LTF'
    ]
}

def get_strategy_info(strategy_code: str) -> dict:
    """Get complete strategy information"""
    return STRATEGY_DOMAINS.get(strategy_code, {})

def get_related_strategies(strategy_code: str) -> list:
    """Get related strategy codes"""
    return STRATEGY_RELATIONSHIPS.get(strategy_code, [])

def classify_content_by_keywords(text: str) -> list:
    """Classify text content into strategy categories based on keywords"""
    text_lower = text.lower()
    matches = []
    
    for strategy, keywords in STRATEGY_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw.lower() in text_lower)
        if score > 0:
            matches.append((strategy, score))
    
    # Sort by score and return strategy codes
    matches.sort(key=lambda x: x[1], reverse=True)
    return [strategy for strategy, score in matches]

def get_all_strategy_concepts() -> dict:
    """Get all concepts organized by strategy"""
    return {
        strategy: info['core_concepts']
        for strategy, info in STRATEGY_DOMAINS.items()
    }
