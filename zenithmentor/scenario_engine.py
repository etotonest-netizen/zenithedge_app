"""
Scenario Engine - Generates replayable market situations
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
import random
import json
from typing import Dict, List, Optional, Tuple
from django.utils import timezone


class ScenarioGenerator:
    """Builds training scenarios from historical data with optional synthetic modifications."""
    
    def __init__(self):
        self.regimes = {
            'trending_bull': {'atr_multiplier': (1.0, 1.5), 'win_rate_threshold': 0.6},
            'trending_bear': {'atr_multiplier': (1.0, 1.5), 'win_rate_threshold': 0.6},
            'ranging': {'atr_multiplier': (0.5, 0.9), 'win_rate_threshold': 0.4},
            'high_volatility': {'atr_multiplier': (2.0, 3.0), 'win_rate_threshold': 0.45},
            'low_volatility': {'atr_multiplier': (0.3, 0.7), 'win_rate_threshold': 0.35},
            'breakout': {'atr_multiplier': (1.5, 2.5), 'win_rate_threshold': 0.55},
            'reversal': {'atr_multiplier': (1.2, 2.0), 'win_rate_threshold': 0.5},
            'news_driven': {'atr_multiplier': (2.5, 4.0), 'win_rate_threshold': 0.5},
        }
    
    def create_scenario_from_historical(self, 
                                       df: pd.DataFrame,
                                       name: str,
                                       strategy_focus: str,
                                       regime: str = 'ranging',
                                       difficulty: int = 1,
                                       volatility_multiplier: float = 1.0,
                                       inject_news: bool = False) -> Dict:
        """
        Create a scenario from a DataFrame of OHLCV data.
        
        Args:
            df: DataFrame with columns [timestamp, open, high, low, close, volume]
            name: Scenario name
            strategy_focus: Primary strategy (e.g., 'trend', 'breakout')
            regime: Market regime classification
            difficulty: 1-10 scale
            volatility_multiplier: Amplify/dampen price movements
            inject_news: Whether to add synthetic news events
        
        Returns:
            Dict containing scenario data ready for Scenario model
        """
        # Ensure timestamp is datetime
        if 'timestamp' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['timestamp']):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Apply volatility modification
        if volatility_multiplier != 1.0:
            df = self._apply_volatility_modification(df.copy(), volatility_multiplier)
        
        # Convert to JSON-serializable format
        candle_data = []
        for _, row in df.iterrows():
            candle = {
                'timestamp': row['timestamp'].isoformat() if isinstance(row['timestamp'], datetime) else str(row['timestamp']),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row.get('volume', 0)),
            }
            candle_data.append(candle)
        
        # Detect session
        session = self._detect_session(df)
        
        # Generate synthetic news if requested
        synthetic_news = []
        if inject_news:
            synthetic_news = self._generate_synthetic_news(df, difficulty)
        
        # Calculate optimal solution (simplified - would be more complex in production)
        optimal_solution = self._calculate_optimal_solution(df, strategy_focus, regime)
        
        # Generate grading criteria
        grading_criteria = self._generate_grading_criteria(difficulty, strategy_focus)
        
        scenario_data = {
            'name': name,
            'description': f"A {regime} scenario focusing on {strategy_focus} strategy",
            'regime': regime,
            'session': session,
            'strategy_focus': strategy_focus,
            'difficulty': difficulty,
            'symbol': 'EURUSD',  # Default, can be parameterized
            'timeframe': '15m',
            'start_date': df['timestamp'].iloc[0],
            'end_date': df['timestamp'].iloc[-1],
            'candle_data': candle_data,
            'has_synthetic_news': inject_news,
            'synthetic_news_events': synthetic_news if inject_news else None,
            'volatility_multiplier': Decimal(str(volatility_multiplier)),
            'optimal_entry_price': optimal_solution['entry'],
            'optimal_stop_loss': optimal_solution['stop'],
            'optimal_take_profit': optimal_solution['target'],
            'optimal_direction': optimal_solution['direction'],
            'grading_criteria': grading_criteria,
            'tags': [regime, strategy_focus, session, f'difficulty_{difficulty}'],
        }
        
        return scenario_data
    
    def _apply_volatility_modification(self, df: pd.DataFrame, multiplier: float) -> pd.DataFrame:
        """Amplify or dampen price movements."""
        # Calculate midpoint
        mid = (df['open'] + df['close']) / 2
        
        # Scale deviations from midpoint
        df['open'] = mid + (df['open'] - mid) * multiplier
        df['high'] = mid + (df['high'] - mid) * multiplier
        df['low'] = mid + (df['low'] - mid) * multiplier
        df['close'] = mid + (df['close'] - mid) * multiplier
        
        return df
    
    def _detect_session(self, df: pd.DataFrame) -> str:
        """Detect which trading session the data primarily covers."""
        if 'timestamp' not in df.columns:
            return 'any'
        
        # Get hour of first candle (UTC)
        first_time = df['timestamp'].iloc[0]
        if isinstance(first_time, str):
            first_time = pd.to_datetime(first_time)
        
        hour = first_time.hour
        
        # Session detection (rough approximation)
        if 0 <= hour < 8:
            return 'asian'
        elif 8 <= hour < 13:
            return 'london'
        elif 13 <= hour < 20:
            return 'newyork'
        else:
            return 'asian'
    
    def _generate_synthetic_news(self, df: pd.DataFrame, difficulty: int) -> List[Dict]:
        """Generate synthetic news events to inject into scenario."""
        news_events = []
        
        # Number of events scales with difficulty
        num_events = min(difficulty // 3, 3)
        
        news_templates = [
            {'impact': 'high', 'title': 'Central Bank Rate Decision Surprise', 'sentiment': 'bullish'},
            {'impact': 'high', 'title': 'Unexpected GDP Data Release', 'sentiment': 'bearish'},
            {'impact': 'medium', 'title': 'Employment Data Beats Expectations', 'sentiment': 'bullish'},
            {'impact': 'medium', 'title': 'Inflation Concerns Rise', 'sentiment': 'bearish'},
            {'impact': 'low', 'title': 'Political Commentary Moves Markets', 'sentiment': 'neutral'},
        ]
        
        for i in range(num_events):
            # Pick random candle to inject news
            candle_index = random.randint(len(df) // 4, 3 * len(df) // 4)
            news = random.choice(news_templates).copy()
            news['candle_index'] = candle_index
            news['timestamp'] = df['timestamp'].iloc[candle_index].isoformat()
            news_events.append(news)
        
        return news_events
    
    def _calculate_optimal_solution(self, df: pd.DataFrame, strategy: str, regime: str) -> Dict:
        """
        Calculate optimal entry/exit for the scenario.
        This is simplified - production would use strategy-specific logic.
        """
        # Simple moving average crossover as baseline
        df_copy = df.copy()
        df_copy['sma_fast'] = df_copy['close'].rolling(10).mean()
        df_copy['sma_slow'] = df_copy['close'].rolling(20).mean()
        
        # Find crossover
        df_copy['signal'] = 0
        df_copy.loc[df_copy['sma_fast'] > df_copy['sma_slow'], 'signal'] = 1
        df_copy.loc[df_copy['sma_fast'] < df_copy['sma_slow'], 'signal'] = -1
        
        # Find first signal change
        df_copy['signal_change'] = df_copy['signal'].diff()
        
        entry_idx = df_copy[df_copy['signal_change'] != 0].index
        if len(entry_idx) == 0:
            # No clear signal, use midpoint
            entry_idx = len(df_copy) // 2
        else:
            entry_idx = entry_idx[0]
        
        entry_price = df_copy.iloc[entry_idx]['close']
        direction = 'long' if df_copy.iloc[entry_idx]['signal'] > 0 else 'short'
        
        # Calculate ATR for stop/target
        df_copy['tr'] = df_copy[['high', 'low', 'close']].apply(
            lambda x: max(x['high'] - x['low'], 
                         abs(x['high'] - x['close']), 
                         abs(x['low'] - x['close'])),
            axis=1
        )
        atr = df_copy['tr'].rolling(14).mean().iloc[entry_idx]
        
        # Handle NaN ATR (use 0.001 as default)
        if pd.isna(atr) or atr == 0:
            atr = 0.001
        
        if direction == 'long':
            stop = entry_price - (2 * atr)
            target = entry_price + (3 * atr)
        else:
            stop = entry_price + (2 * atr)
            target = entry_price - (3 * atr)
        
        return {
            'entry': Decimal(str(round(entry_price, 5))),
            'stop': Decimal(str(round(stop, 5))),
            'target': Decimal(str(round(target, 5))),
            'direction': direction,
        }
    
    def _generate_grading_criteria(self, difficulty: int, strategy: str) -> Dict:
        """Generate grading rubric based on difficulty."""
        base_criteria = {
            'min_pass_score': 70,
            'technical_weight': 0.30,
            'risk_mgmt_weight': 0.25,
            'execution_weight': 0.20,
            'journaling_weight': 0.15,
            'discipline_weight': 0.10,
            'max_acceptable_risk_per_trade': 2.5,  # percent
            'min_reward_risk_ratio': 1.5,
            'max_consecutive_losses_allowed': 3,
        }
        
        # Adjust for difficulty
        if difficulty <= 3:
            base_criteria['min_pass_score'] = 60
            base_criteria['max_acceptable_risk_per_trade'] = 3.0
            base_criteria['min_reward_risk_ratio'] = 1.2
        elif difficulty >= 7:
            base_criteria['min_pass_score'] = 80
            base_criteria['max_acceptable_risk_per_trade'] = 2.0
            base_criteria['min_reward_risk_ratio'] = 2.0
        
        return base_criteria
    
    def sample_historical_window(self, 
                                 full_df: pd.DataFrame, 
                                 window_size_candles: int = 100,
                                 regime_filter: Optional[str] = None) -> pd.DataFrame:
        """
        Sample a random window from historical data, optionally filtered by regime.
        
        Args:
            full_df: Full historical DataFrame
            window_size_candles: Number of candles in scenario
            regime_filter: Optional regime to filter for
        
        Returns:
            Sampled DataFrame window
        """
        if regime_filter:
            # Simple regime detection - would be more sophisticated in production
            full_df = full_df.copy()
            full_df['returns'] = full_df['close'].pct_change()
            full_df['volatility'] = full_df['returns'].rolling(20).std()
            
            if regime_filter == 'trending_bull':
                full_df = full_df[full_df['returns'].rolling(20).mean() > 0]
            elif regime_filter == 'trending_bear':
                full_df = full_df[full_df['returns'].rolling(20).mean() < 0]
            elif regime_filter == 'high_volatility':
                vol_threshold = full_df['volatility'].quantile(0.75)
                full_df = full_df[full_df['volatility'] > vol_threshold]
            elif regime_filter == 'low_volatility':
                vol_threshold = full_df['volatility'].quantile(0.25)
                full_df = full_df[full_df['volatility'] < vol_threshold]
        
        # Ensure we have enough data
        if len(full_df) < window_size_candles:
            return full_df
        
        # Random start index
        max_start = len(full_df) - window_size_candles
        start_idx = random.randint(0, max_start)
        
        return full_df.iloc[start_idx:start_idx + window_size_candles].reset_index(drop=True)


class ScenarioBank:
    """Manages pre-generated scenario collections."""
    
    def __init__(self):
        self.packs = {
            'news_shock': {
                'description': 'High-impact news events with rapid price movements',
                'regime': 'news_driven',
                'difficulty_range': (4, 8),
            },
            'liquidity_sweep': {
                'description': 'Price sweeps key levels before reversing',
                'regime': 'reversal',
                'difficulty_range': (5, 9),
            },
            'low_volatility': {
                'description': 'Range-bound markets with false breakouts',
                'regime': 'ranging',
                'difficulty_range': (3, 6),
            },
            'asian_range': {
                'description': 'Asian session range trading',
                'regime': 'ranging',
                'difficulty_range': (2, 5),
            },
            'trend_continuation': {
                'description': 'Clear trending markets with pullbacks',
                'regime': 'trending_bull',
                'difficulty_range': (1, 4),
            },
        }
    
    def get_pack_scenarios(self, pack_name: str, count: int = 10) -> List[str]:
        """Get scenario IDs from a pack."""
        from .models import Scenario
        
        if pack_name not in self.packs:
            return []
        
        pack_info = self.packs[pack_name]
        
        scenarios = Scenario.objects.filter(
            regime=pack_info['regime'],
            difficulty__gte=pack_info['difficulty_range'][0],
            difficulty__lte=pack_info['difficulty_range'][1],
            is_active=True
        ).order_by('?')[:count]
        
        return [str(s.id) for s in scenarios]


# Singleton instances
scenario_generator = ScenarioGenerator()
scenario_bank = ScenarioBank()
