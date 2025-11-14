"""
Market Regime Detector for Cognition Module
Classifies market state using pandas and technical indicators
"""
import logging
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available")

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")


class RegimeDetector:
    """
    Detects and classifies market regimes from OHLC data
    """
    
    def __init__(self):
        """Initialize regime detector"""
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
    
    def detect_regime(self, ohlc_data: pd.DataFrame) -> Dict:
        """
        Detect current market regime from OHLC data
        
        Args:
            ohlc_data: DataFrame with columns: open, high, low, close, volume
                      Index should be datetime
        
        Returns:
            Dictionary with regime classification and metrics
        """
        if not PANDAS_AVAILABLE or ohlc_data is None or ohlc_data.empty:
            return self._get_default_regime()
        
        try:
            # Calculate technical indicators
            features = self._calculate_features(ohlc_data)
            
            # Classify regime
            regime_type = self._classify_regime(features)
            confidence = self._calculate_confidence(features, regime_type)
            
            # Calculate regime bias
            regime_bias = self._calculate_regime_bias(regime_type, features)
            
            return {
                'regime_type': regime_type,
                'regime_confidence': confidence,
                'trend_strength': features['trend_strength'],
                'volatility_percentile': features['volatility_percentile'],
                'volume_profile': features['volume_profile'],
                'detected_patterns': features['patterns'],
                'feature_vector': {
                    'adx': features['adx'],
                    'atr_percentile': features['atr_percentile'],
                    'bb_width': features['bb_width'],
                    'volume_ratio': features['volume_ratio'],
                    'trend_consistency': features['trend_consistency'],
                },
                'regime_bias': regime_bias,
            }
        
        except Exception as e:
            logger.error(f"Regime detection error: {e}")
            return self._get_default_regime()
    
    def _calculate_features(self, df: pd.DataFrame) -> Dict:
        """
        Calculate technical features for regime classification
        """
        features = {}
        
        # Ensure we have enough data
        if len(df) < 30:
            return self._get_default_features()
        
        # Calculate returns
        df['returns'] = df['close'].pct_change()
        
        # 1. Trend Strength (ADX-like calculation)
        features['trend_strength'] = self._calculate_trend_strength(df)
        features['adx'] = features['trend_strength'] * 100  # Scale to 0-100
        
        # 2. Volatility Metrics
        features['atr'] = self._calculate_atr(df, period=14)
        features['atr_percentile'] = self._calculate_percentile(df, features['atr'])
        features['volatility_percentile'] = features['atr_percentile']
        
        # 3. Bollinger Band Width
        features['bb_width'] = self._calculate_bb_width(df, period=20)
        
        # 4. Volume Profile
        features['volume_ratio'] = self._calculate_volume_ratio(df)
        features['volume_profile'] = features['volume_ratio']
        
        # 5. Trend Consistency
        features['trend_consistency'] = self._calculate_trend_consistency(df)
        
        # 6. Detect Patterns
        features['patterns'] = self._detect_patterns(df)
        
        return features
    
    def _calculate_trend_strength(self, df: pd.DataFrame, period: int = 14) -> float:
        """
        Calculate trend strength (simplified ADX)
        Returns 0 (no trend) to 1 (strong trend)
        """
        # Calculate directional movement
        df['high_diff'] = df['high'].diff()
        df['low_diff'] = -df['low'].diff()
        
        df['plus_dm'] = np.where((df['high_diff'] > df['low_diff']) & (df['high_diff'] > 0),
                                  df['high_diff'], 0)
        df['minus_dm'] = np.where((df['low_diff'] > df['high_diff']) & (df['low_diff'] > 0),
                                   df['low_diff'], 0)
        
        # Calculate True Range
        df['tr'] = self._calculate_true_range(df)
        
        # Smooth with EMA
        plus_di = (df['plus_dm'].rolling(period).sum() / 
                   df['tr'].rolling(period).sum()).fillna(0)
        minus_di = (df['minus_dm'].rolling(period).sum() / 
                    df['tr'].rolling(period).sum()).fillna(0)
        
        # Calculate DX (directional index)
        dx = abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)
        
        # Return latest ADX-like value (0-1 scale)
        adx = dx.rolling(period).mean().iloc[-1]
        return min(1.0, max(0.0, adx))
    
    def _calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        """Calculate True Range"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        tr = self._calculate_true_range(df)
        atr = tr.rolling(period).mean().iloc[-1]
        return atr if not np.isnan(atr) else 0.0
    
    def _calculate_percentile(self, df: pd.DataFrame, value: float, period: int = 30) -> float:
        """
        Calculate percentile of current value in recent period
        """
        if len(df) < period:
            return 0.5
        
        recent_closes = df['close'].iloc[-period:]
        percentile = (recent_closes < df['close'].iloc[-1]).sum() / period
        return percentile
    
    def _calculate_bb_width(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        Calculate Bollinger Band width (normalized)
        """
        sma = df['close'].rolling(period).mean()
        std = df['close'].rolling(period).std()
        
        upper = sma + (2 * std)
        lower = sma - (2 * std)
        width = (upper - lower) / sma
        
        return width.iloc[-1] if not np.isnan(width.iloc[-1]) else 0.1
    
    def _calculate_volume_ratio(self, df: pd.DataFrame, period: int = 20) -> float:
        """
        Calculate current volume vs average volume
        """
        if 'volume' not in df.columns:
            return 1.0
        
        avg_volume = df['volume'].rolling(period).mean().iloc[-1]
        current_volume = df['volume'].iloc[-1]
        
        if avg_volume == 0:
            return 1.0
        
        ratio = current_volume / avg_volume
        return min(3.0, ratio)  # Cap at 3x
    
    def _calculate_trend_consistency(self, df: pd.DataFrame, period: int = 10) -> float:
        """
        Calculate how consistent the trend direction is
        Returns 0 (inconsistent) to 1 (very consistent)
        """
        # Look at last N candles
        recent = df.iloc[-period:]
        
        # Count higher highs and higher lows (uptrend)
        higher_highs = (recent['high'].diff() > 0).sum()
        higher_lows = (recent['low'].diff() > 0).sum()
        
        # Count lower highs and lower lows (downtrend)
        lower_highs = (recent['high'].diff() < 0).sum()
        lower_lows = (recent['low'].diff() < 0).sum()
        
        # Consistency is the max of uptrend or downtrend signals
        up_consistency = (higher_highs + higher_lows) / (2 * period)
        down_consistency = (lower_highs + lower_lows) / (2 * period)
        
        return max(up_consistency, down_consistency)
    
    def _detect_patterns(self, df: pd.DataFrame) -> List[str]:
        """
        Detect common price patterns
        """
        patterns = []
        
        if len(df) < 20:
            return patterns
        
        recent = df.iloc[-20:]
        
        # Higher highs and higher lows = uptrend
        if ((recent['high'].iloc[-5:] > recent['high'].iloc[-10:-5].max()).any() and
            (recent['low'].iloc[-5:] > recent['low'].iloc[-10:-5].min()).any()):
            patterns.append('higher_highs')
        
        # Lower highs and lower lows = downtrend
        if ((recent['high'].iloc[-5:] < recent['high'].iloc[-10:-5].min()).any() and
            (recent['low'].iloc[-5:] < recent['low'].iloc[-10:-5].max()).any()):
            patterns.append('lower_lows')
        
        # Range-bound (price within 2% of 20-period range)
        high_range = recent['high'].max()
        low_range = recent['low'].min()
        current_price = df['close'].iloc[-1]
        
        range_pct = (high_range - low_range) / current_price
        if range_pct < 0.02:
            patterns.append('range_bound')
        
        # Squeeze (low volatility)
        if self._calculate_bb_width(df) < 0.05:
            patterns.append('squeeze')
        
        return patterns
    
    def _classify_regime(self, features: Dict) -> str:
        """
        Classify market regime based on features
        """
        trend_strength = features['trend_strength']
        volatility = features['volatility_percentile']
        bb_width = features['bb_width']
        patterns = features['patterns']
        
        # Strong trend: high ADX, consistent direction
        if trend_strength > 0.6 and features['trend_consistency'] > 0.7:
            return 'strong_trend'
        
        # Weak trend: moderate ADX
        elif trend_strength > 0.4:
            return 'weak_trend'
        
        # Squeeze: low volatility, tight range
        elif bb_width < 0.05 or 'squeeze' in patterns:
            return 'squeeze'
        
        # High volatility: large ATR percentile
        elif volatility > 0.8 and bb_width > 0.15:
            return 'volatile'
        
        # Low volatility/quiet
        elif volatility < 0.3 and bb_width < 0.08:
            return 'quiet'
        
        # Default: choppy/range-bound
        else:
            return 'choppy'
    
    def _calculate_confidence(self, features: Dict, regime_type: str) -> float:
        """
        Calculate confidence in regime classification
        """
        # Base confidence on feature clarity
        confidence = 0.5
        
        if regime_type in ['strong_trend', 'weak_trend']:
            # Confidence increases with trend strength and consistency
            confidence = (features['trend_strength'] * 0.6 + 
                         features['trend_consistency'] * 0.4)
        
        elif regime_type == 'squeeze':
            # Confidence based on how tight the squeeze is
            confidence = max(0.3, 1.0 - features['bb_width'] * 10)
        
        elif regime_type in ['volatile', 'quiet']:
            # Confidence based on volatility extremeness
            vol_extreme = abs(features['volatility_percentile'] - 0.5) * 2
            confidence = 0.5 + vol_extreme * 0.5
        
        else:  # choppy
            # Lower confidence for choppy markets
            confidence = 0.4
        
        return min(1.0, max(0.3, confidence))
    
    def _calculate_regime_bias(self, regime_type: str, features: Dict) -> float:
        """
        Calculate trading bias based on regime
        Returns -1 (avoid) to +1 (favorable)
        """
        if regime_type == 'strong_trend':
            return 0.8 * features['trend_strength']
        
        elif regime_type == 'weak_trend':
            return 0.4
        
        elif regime_type == 'squeeze':
            # Slightly positive (breakout opportunity)
            return 0.2
        
        elif regime_type == 'choppy':
            # Negative bias (avoid)
            return -0.5
        
        elif regime_type == 'volatile':
            # Depends on volatility level
            if features['volatility_percentile'] > 0.9:
                return -0.6  # Too volatile
            else:
                return 0.1
        
        elif regime_type == 'quiet':
            # Slightly negative (low opportunity)
            return -0.2
        
        return 0.0
    
    def _get_default_regime(self) -> Dict:
        """Return default regime for errors"""
        return {
            'regime_type': 'choppy',
            'regime_confidence': 0.3,
            'trend_strength': 0.3,
            'volatility_percentile': 0.5,
            'volume_profile': 1.0,
            'detected_patterns': [],
            'feature_vector': {},
            'regime_bias': 0.0,
        }
    
    def _get_default_features(self) -> Dict:
        """Return default features"""
        return {
            'trend_strength': 0.3,
            'adx': 30,
            'atr': 0.0,
            'atr_percentile': 0.5,
            'volatility_percentile': 0.5,
            'bb_width': 0.1,
            'volume_ratio': 1.0,
            'volume_profile': 1.0,
            'trend_consistency': 0.5,
            'patterns': [],
        }


# Convenience function
def detect_market_regime(ohlc_data: pd.DataFrame) -> Dict:
    """
    Detect market regime from OHLC data
    
    Args:
        ohlc_data: DataFrame with OHLC + volume data
        
    Returns:
        Dictionary with regime classification
    """
    detector = RegimeDetector()
    return detector.detect_regime(ohlc_data)
