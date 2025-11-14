"""
Strategy Detectors Module

Implements all 10 trading strategy detectors:
1. SMC (Smart Money Concepts)
2. ICT (Inner Circle Trader)
3. Trend Following
4. Breakout
5. Mean Reversion
6. Squeeze
7. Scalping
8. VWAP
9. Supply/Demand
10. Multi-Timeframe

Each detector returns structured metadata compatible with Signal model.
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, time
from dataclasses import dataclass, asdict

from .indicators import (
    sma, ema, rsi, atr, bollinger_bands, keltner_channels, 
    adx, vwap, market_structure, calculate_all_indicators
)
from .smc import detect_smc


@dataclass
class StrategySignal:
    """Universal signal structure for all strategies"""
    timestamp: datetime
    symbol: str
    timeframe: str
    side: str  # 'buy' or 'sell'
    price: float
    stop_loss: float
    take_profit: float
    confidence: float  # 0-100
    strategy: str
    regime: str  # 'trending', 'ranging', 'volatile', 'quiet'
    
    # Metadata
    entry_reason: str
    structure_tags: List[str]
    extra: Dict
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class ICTDetector:
    """
    Inner Circle Trader (ICT) strategy detector
    
    Features:
    - Session-based trading (Asian, London, New York killzones)
    - Wick rejection patterns
    - Fair Value Gaps (FVG)
    - Liquidity grabs
    """
    
    def __init__(self, asian_session=(0, 8), london_session=(8, 16), newyork_session=(13, 22)):
        self.asian_session = asian_session
        self.london_session = london_session
        self.newyork_session = newyork_session
    
    def is_killzone(self, timestamp: datetime) -> Optional[str]:
        """Check if timestamp is in a trading killzone"""
        hour = timestamp.hour
        
        if self.london_session[0] <= hour < self.london_session[1]:
            return 'london'
        elif self.newyork_session[0] <= hour < self.newyork_session[1]:
            return 'newyork'
        elif self.asian_session[0] <= hour < self.asian_session[1]:
            return 'asian'
        return None
    
    def detect_wick_rejection(self, df: pd.DataFrame, min_wick_ratio: float = 2.0) -> List[Dict]:
        """Detect strong wick rejections"""
        rejections = []
        
        for i in range(2, len(df)):
            bar = df.iloc[i]
            body = abs(bar['close'] - bar['open'])
            
            if body == 0:
                continue
            
            # Bullish rejection (long lower wick)
            lower_wick = min(bar['open'], bar['close']) - bar['low']
            if lower_wick / body > min_wick_ratio:
                rejections.append({
                    'type': 'bullish_rejection',
                    'timestamp': df.index[i],
                    'price': bar['low'],
                    'strength': lower_wick / body
                })
            
            # Bearish rejection (long upper wick)
            upper_wick = bar['high'] - max(bar['open'], bar['close'])
            if upper_wick / body > min_wick_ratio:
                rejections.append({
                    'type': 'bearish_rejection',
                    'timestamp': df.index[i],
                    'price': bar['high'],
                    'strength': upper_wick / body
                })
        
        return rejections
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[StrategySignal]:
        """Main ICT detection logic"""
        signals = []
        
        if len(df) < 50:
            return signals
        
        # Calculate indicators
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        current_time = df.index[-1]
        
        # Check if in killzone
        killzone = self.is_killzone(current_time)
        if not killzone:
            return signals  # Only trade during killzones
        
        # Detect wick rejections
        rejections = self.detect_wick_rejection(df.tail(20))
        
        # Get recent FVGs from SMC module
        from .smc import SMCDetector
        smc = SMCDetector()
        fvgs = smc.detect_fvg(df.tail(50))
        
        # Look for bullish setups
        recent_bullish_rejection = any(r['type'] == 'bullish_rejection' for r in rejections[-3:])
        unfilled_bullish_fvg = any(not fvg.filled and fvg.type == 'bullish' for fvg in fvgs[-5:])
        
        if recent_bullish_rejection and unfilled_bullish_fvg:
            atr_val = df['atr_14'].iloc[-1]
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='buy',
                price=float(current_bar['close']),
                stop_loss=float(current_bar['close'] - atr_val * 1.5),
                take_profit=float(current_bar['close'] + atr_val * 3),
                confidence=75.0,
                strategy='ICT',
                regime='trending',
                entry_reason=f'{killzone}_killzone_bullish_rejection',
                structure_tags=['wick_rejection', 'fvg', killzone],
                extra={'killzone': killzone, 'rejections': len(rejections)}
            )
            signals.append(signal)
        
        # Look for bearish setups
        recent_bearish_rejection = any(r['type'] == 'bearish_rejection' for r in rejections[-3:])
        unfilled_bearish_fvg = any(not fvg.filled and fvg.type == 'bearish' for fvg in fvgs[-5:])
        
        if recent_bearish_rejection and unfilled_bearish_fvg:
            atr_val = df['atr_14'].iloc[-1]
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='sell',
                price=float(current_bar['close']),
                stop_loss=float(current_bar['close'] + atr_val * 1.5),
                take_profit=float(current_bar['close'] - atr_val * 3),
                confidence=75.0,
                strategy='ICT',
                regime='trending',
                entry_reason=f'{killzone}_killzone_bearish_rejection',
                structure_tags=['wick_rejection', 'fvg', killzone],
                extra={'killzone': killzone, 'rejections': len(rejections)}
            )
            signals.append(signal)
        
        return signals


class TrendFollowingDetector:
    """
    Trend Following strategy
    
    Features:
    - MA crossovers (EMA 9/21, SMA 50/200)
    - ADX strength confirmation (>25)
    - Higher Highs/Higher Lows (HH/HL) for uptrend
    - Lower Highs/Lower Lows (LH/LL) for downtrend
    """
    
    def __init__(self, fast_ma=9, slow_ma=21, adx_threshold=25):
        self.fast_ma = fast_ma
        self.slow_ma = slow_ma
        self.adx_threshold = adx_threshold
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[StrategySignal]:
        """Detect trend following signals"""
        signals = []
        
        if len(df) < 50:
            return signals
        
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        prev_bar = df.iloc[-2]
        current_time = df.index[-1]
        
        # Check MA crossover
        ema_fast_curr = current_bar['ema_9']
        ema_slow_curr = current_bar['ema_21']
        ema_fast_prev = prev_bar['ema_9']
        ema_slow_prev = prev_bar['ema_21']
        
        # ADX strength
        adx_val = current_bar['adx']
        
        # Market structure
        structure = market_structure(df.tail(50), swing_period=5)
        
        # Bullish crossover + strong trend
        if (ema_fast_prev <= ema_slow_prev and 
            ema_fast_curr > ema_slow_curr and
            adx_val > self.adx_threshold and
            structure['trend'] == 'uptrend'):
            
            atr_val = current_bar['atr_14']
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='buy',
                price=float(current_bar['close']),
                stop_loss=float(current_bar['close'] - atr_val * 2),
                take_profit=float(current_bar['close'] + atr_val * 4),
                confidence=min(95, 60 + (adx_val - self.adx_threshold)),
                strategy='Trend',
                regime='trending',
                entry_reason='bullish_ma_crossover_strong_trend',
                structure_tags=['ema_crossover', 'uptrend', 'adx_strong'],
                extra={'adx': float(adx_val), 'market_structure': structure}
            )
            signals.append(signal)
        
        # Bearish crossover + strong trend
        elif (ema_fast_prev >= ema_slow_prev and 
              ema_fast_curr < ema_slow_curr and
              adx_val > self.adx_threshold and
              structure['trend'] == 'downtrend'):
            
            atr_val = current_bar['atr_14']
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='sell',
                price=float(current_bar['close']),
                stop_loss=float(current_bar['close'] + atr_val * 2),
                take_profit=float(current_bar['close'] - atr_val * 4),
                confidence=min(95, 60 + (adx_val - self.adx_threshold)),
                strategy='Trend',
                regime='trending',
                entry_reason='bearish_ma_crossover_strong_trend',
                structure_tags=['ema_crossover', 'downtrend', 'adx_strong'],
                extra={'adx': float(adx_val), 'market_structure': structure}
            )
            signals.append(signal)
        
        return signals


class BreakoutDetector:
    """
    Breakout strategy
    
    Features:
    - Donchian channel breakouts
    - Volume spike confirmation
    - Consolidation detection
    """
    
    def __init__(self, donchian_period=20, volume_threshold=1.5):
        self.donchian_period = donchian_period
        self.volume_threshold = volume_threshold
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[StrategySignal]:
        """Detect breakout signals"""
        signals = []
        
        if len(df) < self.donchian_period + 10:
            return signals
        
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        current_time = df.index[-1]
        
        # Calculate Donchian channels
        window = df['high'].rolling(window=self.donchian_period)
        dc_upper = window.max()
        dc_lower = df['low'].rolling(window=self.donchian_period).min()
        
        # Average volume
        avg_volume = df['volume'].rolling(window=20).mean()
        
        # Bullish breakout
        if (current_bar['close'] > dc_upper.iloc[-2] and
            current_bar['volume'] > avg_volume.iloc[-1] * self.volume_threshold):
            
            atr_val = current_bar['atr_14']
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='buy',
                price=float(current_bar['close']),
                stop_loss=float(dc_lower.iloc[-1]),
                take_profit=float(current_bar['close'] + (current_bar['close'] - dc_lower.iloc[-1]) * 2),
                confidence=80.0,
                strategy='Breakout',
                regime='volatile',
                entry_reason='bullish_donchian_breakout_volume',
                structure_tags=['breakout', 'volume_spike', 'consolidation_exit'],
                extra={'volume_ratio': float(current_bar['volume'] / avg_volume.iloc[-1])}
            )
            signals.append(signal)
        
        # Bearish breakout
        elif (current_bar['close'] < dc_lower.iloc[-2] and
              current_bar['volume'] > avg_volume.iloc[-1] * self.volume_threshold):
            
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='sell',
                price=float(current_bar['close']),
                stop_loss=float(dc_upper.iloc[-1]),
                take_profit=float(current_bar['close'] - (dc_upper.iloc[-1] - current_bar['close']) * 2),
                confidence=80.0,
                strategy='Breakout',
                regime='volatile',
                entry_reason='bearish_donchian_breakout_volume',
                structure_tags=['breakout', 'volume_spike', 'consolidation_exit'],
                extra={'volume_ratio': float(current_bar['volume'] / avg_volume.iloc[-1])}
            )
            signals.append(signal)
        
        return signals


class MeanReversionDetector:
    """
    Mean Reversion strategy
    
    Features:
    - RSI oversold/overbought
    - Bollinger Band extremes
    - Price returns to mean
    """
    
    def __init__(self, rsi_oversold=30, rsi_overbought=70):
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[StrategySignal]:
        """Detect mean reversion signals"""
        signals = []
        
        if len(df) < 50:
            return signals
        
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        current_time = df.index[-1]
        
        rsi_val = current_bar['rsi_14']
        bb_upper = current_bar['bb_upper']
        bb_lower = current_bar['bb_lower']
        bb_middle = current_bar['bb_middle']
        close = current_bar['close']
        
        # Bullish mean reversion (oversold)
        if rsi_val < self.rsi_oversold and close < bb_lower:
            atr_val = current_bar['atr_14']
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='buy',
                price=float(close),
                stop_loss=float(close - atr_val * 1.5),
                take_profit=float(bb_middle),
                confidence=min(95, 70 + (self.rsi_oversold - rsi_val)),
                strategy='MeanReversion',
                regime='ranging',
                entry_reason='oversold_bb_touch',
                structure_tags=['rsi_oversold', 'bb_lower', 'mean_reversion'],
                extra={'rsi': float(rsi_val), 'distance_from_bb': float((bb_lower - close) / atr_val)}
            )
            signals.append(signal)
        
        # Bearish mean reversion (overbought)
        elif rsi_val > self.rsi_overbought and close > bb_upper:
            atr_val = current_bar['atr_14']
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='sell',
                price=float(close),
                stop_loss=float(close + atr_val * 1.5),
                take_profit=float(bb_middle),
                confidence=min(95, 70 + (rsi_val - self.rsi_overbought)),
                strategy='MeanReversion',
                regime='ranging',
                entry_reason='overbought_bb_touch',
                structure_tags=['rsi_overbought', 'bb_upper', 'mean_reversion'],
                extra={'rsi': float(rsi_val), 'distance_from_bb': float((close - bb_upper) / atr_val)}
            )
            signals.append(signal)
        
        return signals


class SqueezeDetector:
    """
    Squeeze strategy (Bollinger Bands inside Keltner Channels)
    
    Features:
    - Volatility compression detection
    - Breakout from squeeze
    """
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[StrategySignal]:
        """Detect squeeze breakout signals"""
        signals = []
        
        if len(df) < 50:
            return signals
        
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        prev_bar = df.iloc[-2]
        current_time = df.index[-1]
        
        # Check if BB is inside KC (squeeze)
        bb_width = current_bar['bb_upper'] - current_bar['bb_lower']
        kc_width = current_bar['kc_upper'] - current_bar['kc_lower']
        
        prev_bb_width = prev_bar['bb_upper'] - prev_bar['bb_lower']
        prev_kc_width = prev_bar['kc_upper'] - prev_bar['kc_lower']
        
        # Was in squeeze, now breaking out
        was_in_squeeze = (prev_bb_width < prev_kc_width)
        breaking_out = (bb_width >= kc_width)
        
        if was_in_squeeze and breaking_out:
            # Determine direction
            close = current_bar['close']
            sma_20 = current_bar['sma_20']
            
            atr_val = current_bar['atr_14']
            
            if close > sma_20:  # Bullish breakout
                signal = StrategySignal(
                    timestamp=current_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    side='buy',
                    price=float(close),
                    stop_loss=float(close - atr_val * 2),
                    take_profit=float(close + atr_val * 4),
                    confidence=78.0,
                    strategy='Squeeze',
                    regime='volatile',
                    entry_reason='bullish_squeeze_breakout',
                    structure_tags=['squeeze_release', 'volatility_expansion', 'breakout'],
                    extra={'bb_kc_ratio': float(bb_width / kc_width)}
                )
                signals.append(signal)
            
            elif close < sma_20:  # Bearish breakout
                signal = StrategySignal(
                    timestamp=current_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    side='sell',
                    price=float(close),
                    stop_loss=float(close + atr_val * 2),
                    take_profit=float(close - atr_val * 4),
                    confidence=78.0,
                    strategy='Squeeze',
                    regime='volatile',
                    entry_reason='bearish_squeeze_breakout',
                    structure_tags=['squeeze_release', 'volatility_expansion', 'breakout'],
                    extra={'bb_kc_ratio': float(bb_width / kc_width)}
                )
                signals.append(signal)
        
        return signals


class ScalpingDetector:
    """
    Scalping strategy (1m/5m only)
    
    Features:
    - RSI-3 extremes
    - Fast EMA crossovers (5/13)
    - Quick in-and-out trades
    """
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[StrategySignal]:
        """Detect scalping signals"""
        signals = []
        
        # Only trade on 1m or 5m timeframes
        if timeframe not in ['1', '5', '1M', '5M']:
            return signals
        
        if len(df) < 30:
            return signals
        
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        prev_bar = df.iloc[-2]
        current_time = df.index[-1]
        
        rsi_3 = current_bar['rsi_3']
        
        # Fast EMA crossover
        ema_5 = ema(df['close'], 5)
        ema_13 = ema(df['close'], 13)
        
        ema_5_curr = ema_5.iloc[-1]
        ema_13_curr = ema_13.iloc[-1]
        ema_5_prev = ema_5.iloc[-2]
        ema_13_prev = ema_13.iloc[-2]
        
        atr_val = current_bar['atr_14']
        
        # Bullish scalp (RSI oversold + EMA cross)
        if rsi_3 < 10 and ema_5_prev <= ema_13_prev and ema_5_curr > ema_13_curr:
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='buy',
                price=float(current_bar['close']),
                stop_loss=float(current_bar['close'] - atr_val * 1.0),
                take_profit=float(current_bar['close'] + atr_val * 1.5),
                confidence=72.0,
                strategy='Scalping',
                regime='quiet',
                entry_reason='rsi3_oversold_ema_cross',
                structure_tags=['scalp', 'rsi3', 'fast_ema'],
                extra={'rsi_3': float(rsi_3), 'timeframe': timeframe}
            )
            signals.append(signal)
        
        # Bearish scalp
        elif rsi_3 > 90 and ema_5_prev >= ema_13_prev and ema_5_curr < ema_13_curr:
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='sell',
                price=float(current_bar['close']),
                stop_loss=float(current_bar['close'] + atr_val * 1.0),
                take_profit=float(current_bar['close'] - atr_val * 1.5),
                confidence=72.0,
                strategy='Scalping',
                regime='quiet',
                entry_reason='rsi3_overbought_ema_cross',
                structure_tags=['scalp', 'rsi3', 'fast_ema'],
                extra={'rsi_3': float(rsi_3), 'timeframe': timeframe}
            )
            signals.append(signal)
        
        return signals


class VWAPDetector:
    """
    VWAP strategy
    
    Features:
    - Price reclaiming VWAP
    - Trading above/below VWAP
    - VWAP deviations
    """
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[StrategySignal]:
        """Detect VWAP signals"""
        signals = []
        
        if len(df) < 50 or 'volume' not in df.columns:
            return signals
        
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        prev_bar = df.iloc[-2]
        current_time = df.index[-1]
        
        if 'vwap' not in df.columns:
            return signals
        
        vwap_curr = current_bar['vwap']
        close_curr = current_bar['close']
        close_prev = prev_bar['close']
        vwap_prev = prev_bar['vwap']
        
        atr_val = current_bar['atr_14']
        
        # Bullish VWAP reclaim
        if close_prev < vwap_prev and close_curr > vwap_curr:
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='buy',
                price=float(close_curr),
                stop_loss=float(vwap_curr - atr_val),
                take_profit=float(close_curr + atr_val * 2),
                confidence=76.0,
                strategy='VWAP',
                regime='trending',
                entry_reason='vwap_reclaim_bullish',
                structure_tags=['vwap_cross', 'reclaim', 'momentum'],
                extra={'vwap': float(vwap_curr), 'distance_from_vwap': float((close_curr - vwap_curr) / atr_val)}
            )
            signals.append(signal)
        
        # Bearish VWAP breakdown
        elif close_prev > vwap_prev and close_curr < vwap_curr:
            signal = StrategySignal(
                timestamp=current_time,
                symbol=symbol,
                timeframe=timeframe,
                side='sell',
                price=float(close_curr),
                stop_loss=float(vwap_curr + atr_val),
                take_profit=float(close_curr - atr_val * 2),
                confidence=76.0,
                strategy='VWAP',
                regime='trending',
                entry_reason='vwap_breakdown_bearish',
                structure_tags=['vwap_cross', 'breakdown', 'momentum'],
                extra={'vwap': float(vwap_curr), 'distance_from_vwap': float((vwap_curr - close_curr) / atr_val)}
            )
            signals.append(signal)
        
        return signals


class SupplyDemandDetector:
    """
    Supply/Demand zones strategy
    
    Features:
    - Displacement candle detection
    - Rally-Base-Rally / Drop-Base-Drop patterns
    - Zone validation
    """
    
    def __init__(self, displacement_threshold=2.0):
        self.displacement_threshold = displacement_threshold
    
    def detect_displacement(self, df: pd.DataFrame) -> List[Dict]:
        """Detect displacement candles (strong impulsive moves)"""
        displacements = []
        
        avg_body = abs(df['close'] - df['open']).rolling(window=20).mean()
        
        for i in range(20, len(df)):
            bar = df.iloc[i]
            body = abs(bar['close'] - bar['open'])
            avg = avg_body.iloc[i]
            
            if body > avg * self.displacement_threshold:
                direction = 'bullish' if bar['close'] > bar['open'] else 'bearish'
                displacements.append({
                    'index': i,
                    'timestamp': df.index[i],
                    'direction': direction,
                    'strength': body / avg,
                    'high': bar['high'],
                    'low': bar['low']
                })
        
        return displacements
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[StrategySignal]:
        """Detect supply/demand signals"""
        signals = []
        
        if len(df) < 50:
            return signals
        
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        current_time = df.index[-1]
        
        # Detect displacement candles
        displacements = self.detect_displacement(df.tail(30))
        
        if not displacements:
            return signals
        
        # Find most recent strong displacement
        recent_displacement = displacements[-1]
        close = current_bar['close']
        atr_val = current_bar['atr_14']
        
        # Check if price is returning to the base before displacement
        if recent_displacement['direction'] == 'bullish':
            # Price returning to demand zone
            demand_zone_high = recent_displacement['low'] + atr_val * 0.5
            demand_zone_low = recent_displacement['low']
            
            if demand_zone_low <= close <= demand_zone_high:
                signal = StrategySignal(
                    timestamp=current_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    side='buy',
                    price=float(close),
                    stop_loss=float(demand_zone_low - atr_val * 0.5),
                    take_profit=float(close + (recent_displacement['high'] - close)),
                    confidence=81.0,
                    strategy='SupplyDemand',
                    regime='trending',
                    entry_reason='demand_zone_test',
                    structure_tags=['demand_zone', 'displacement', 'rally_base_rally'],
                    extra={'displacement_strength': recent_displacement['strength'], 'zone': 'demand'}
                )
                signals.append(signal)
        
        elif recent_displacement['direction'] == 'bearish':
            # Price returning to supply zone
            supply_zone_low = recent_displacement['high'] - atr_val * 0.5
            supply_zone_high = recent_displacement['high']
            
            if supply_zone_low <= close <= supply_zone_high:
                signal = StrategySignal(
                    timestamp=current_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    side='sell',
                    price=float(close),
                    stop_loss=float(supply_zone_high + atr_val * 0.5),
                    take_profit=float(close - (close - recent_displacement['low'])),
                    confidence=81.0,
                    strategy='SupplyDemand',
                    regime='trending',
                    entry_reason='supply_zone_test',
                    structure_tags=['supply_zone', 'displacement', 'drop_base_drop'],
                    extra={'displacement_strength': recent_displacement['strength'], 'zone': 'supply'}
                )
                signals.append(signal)
        
        return signals


class MultiTimeframeDetector:
    """
    Multi-Timeframe (MTF) strategy
    
    Features:
    - Higher timeframe trend alignment
    - Lower timeframe entry signals
    - Confluence scoring
    """
    
    def __init__(self, htf_multiplier=4):
        self.htf_multiplier = htf_multiplier
    
    def get_higher_timeframe(self, timeframe: str) -> str:
        """Get higher timeframe"""
        tf_map = {
            '1': '5', '5': '15', '15': '1H', '30': '1H',
            '1H': '4H', '4H': 'D', 'D': 'W'
        }
        return tf_map.get(timeframe, 'D')
    
    def detect(self, df: pd.DataFrame, symbol: str, timeframe: str, htf_df: Optional[pd.DataFrame] = None) -> List[StrategySignal]:
        """
        Detect MTF signals
        
        Note: htf_df should be pre-fetched higher timeframe data
        """
        signals = []
        
        if len(df) < 50:
            return signals
        
        df = calculate_all_indicators(df)
        current_bar = df.iloc[-1]
        current_time = df.index[-1]
        
        # If no HTF data provided, resample current df
        if htf_df is None:
            # Simple approach: use trend from longer lookback
            htf_structure = market_structure(df.tail(200), swing_period=20)
        else:
            htf_structure = market_structure(htf_df, swing_period=10)
        
        # LTF structure
        ltf_structure = market_structure(df.tail(50), swing_period=5)
        
        # Check for alignment
        if htf_structure['trend'] == 'uptrend' and ltf_structure['trend'] == 'uptrend':
            # Look for pullback entry on LTF
            ema_21 = current_bar['ema_21']
            close = current_bar['close']
            
            if close < ema_21 * 1.01 and close > ema_21 * 0.99:  # Near EMA
                atr_val = current_bar['atr_14']
                signal = StrategySignal(
                    timestamp=current_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    side='buy',
                    price=float(close),
                    stop_loss=float(ltf_structure['last_swing_low']),
                    take_profit=float(close + atr_val * 4),
                    confidence=88.0,
                    strategy='MultiTF',
                    regime='trending',
                    entry_reason='htf_ltf_bullish_alignment',
                    structure_tags=['mtf_alignment', 'uptrend', 'pullback_entry'],
                    extra={'htf_trend': htf_structure['trend'], 'ltf_trend': ltf_structure['trend']}
                )
                signals.append(signal)
        
        elif htf_structure['trend'] == 'downtrend' and ltf_structure['trend'] == 'downtrend':
            ema_21 = current_bar['ema_21']
            close = current_bar['close']
            
            if close > ema_21 * 0.99 and close < ema_21 * 1.01:  # Near EMA
                atr_val = current_bar['atr_14']
                signal = StrategySignal(
                    timestamp=current_time,
                    symbol=symbol,
                    timeframe=timeframe,
                    side='sell',
                    price=float(close),
                    stop_loss=float(ltf_structure['last_swing_high']),
                    take_profit=float(close - atr_val * 4),
                    confidence=88.0,
                    strategy='MultiTF',
                    regime='trending',
                    entry_reason='htf_ltf_bearish_alignment',
                    structure_tags=['mtf_alignment', 'downtrend', 'pullback_entry'],
                    extra={'htf_trend': htf_structure['trend'], 'ltf_trend': ltf_structure['trend']}
                )
                signals.append(signal)
        
        return signals


# Strategy registry
STRATEGY_DETECTORS = {
    'SMC': lambda: detect_smc,  # SMC is a function, not class
    'ICT': ICTDetector,
    'Trend': TrendFollowingDetector,
    'Breakout': BreakoutDetector,
    'MeanReversion': MeanReversionDetector,
    'Squeeze': SqueezeDetector,
    'Scalping': ScalpingDetector,
    'VWAP': VWAPDetector,
    'SupplyDemand': SupplyDemandDetector,
    'MultiTF': MultiTimeframeDetector,
}


def detect_all_strategies(df: pd.DataFrame, symbol: str, timeframe: str, 
                         strategies: Optional[List[str]] = None) -> List[Dict]:
    """
    Run all strategy detectors on dataframe
    
    Args:
        df: OHLCV DataFrame
        symbol: Trading symbol
        timeframe: Timeframe string
        strategies: List of strategy names to run (None = all)
    
    Returns:
        List of signal dictionaries
    """
    all_signals = []
    
    if strategies is None:
        strategies = list(STRATEGY_DETECTORS.keys())
    
    for strategy_name in strategies:
        if strategy_name not in STRATEGY_DETECTORS:
            continue
        
        detector_class = STRATEGY_DETECTORS[strategy_name]
        
        try:
            # SMC is special case (function not class)
            if strategy_name == 'SMC':
                signals = detect_smc(df, symbol, timeframe)
                all_signals.extend(signals)
            else:
                # Instantiate detector and run
                detector = detector_class()
                signals = detector.detect(df, symbol, timeframe)
                # Convert StrategySignal objects to dicts
                all_signals.extend([s.to_dict() for s in signals])
        
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error in {strategy_name} detector: {e}", exc_info=True)
            continue
    
    return all_signals


def detect_strategy(strategy_name: str, df: pd.DataFrame, symbol: str, 
                   timeframe: str, **kwargs) -> List[Dict]:
    """
    Run specific strategy detector
    
    Args:
        strategy_name: Name of strategy (SMC, ICT, Trend, etc.)
        df: OHLCV DataFrame
        symbol: Trading symbol
        timeframe: Timeframe string
        **kwargs: Additional parameters for detector
    
    Returns:
        List of signal dictionaries
    """
    if strategy_name not in STRATEGY_DETECTORS:
        raise ValueError(f"Unknown strategy: {strategy_name}")
    
    detector_class = STRATEGY_DETECTORS[strategy_name]
    
    if strategy_name == 'SMC':
        return detect_smc(df, symbol, timeframe, **kwargs)
    else:
        detector = detector_class(**kwargs) if kwargs else detector_class()
        signals = detector.detect(df, symbol, timeframe)
        return [s.to_dict() for s in signals]
