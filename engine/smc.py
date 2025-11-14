"""
Smart Money Concepts (SMC) Detection Engine

Implements advanced market structure analysis including:
- Swing High/Low detection
- Break of Structure (BOS) and Change of Character (CHoCH)
- Order Block (OB) detection and validation
- Fair Value Gap (FVG) detection
- Liquidity sweeps and stop hunts
- Equal Highs/Lows (EQH/EQL)
- Premium/Discount zones
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SwingPoint:
    """Represents a swing high or swing low"""
    index: int
    timestamp: datetime
    price: float
    type: str  # 'high' or 'low'
    broken: bool = False


@dataclass
class OrderBlock:
    """Represents an Order Block"""
    start_index: int
    end_index: int
    start_time: datetime
    end_time: datetime
    high: float
    low: float
    type: str  # 'bullish' or 'bearish'
    strength: float  # 0-100
    touched: bool = False
    validated: bool = False


@dataclass
class FairValueGap:
    """Represents a Fair Value Gap"""
    index: int
    timestamp: datetime
    top: float
    bottom: float
    type: str  # 'bullish' or 'bearish'
    filled: bool = False
    fill_percent: float = 0.0


@dataclass
class SMCSignal:
    """Complete SMC signal with all metadata"""
    timestamp: datetime
    symbol: str
    timeframe: str
    side: str  # 'buy' or 'sell'
    price: float
    stop_loss: float
    take_profit: float
    confidence: float
    
    # SMC-specific metadata
    signal_type: str  # 'ob_retest', 'fvg_fill', 'bos_continuation', etc.
    market_structure: str  # 'bullish', 'bearish', 'ranging'
    order_blocks: List[Dict]
    fvgs: List[Dict]
    swing_points: List[Dict]
    liquidity_levels: List[Dict]
    
    # Additional context
    atr: float
    volatility_regime: str  # 'low', 'normal', 'high'
    premium_discount: str  # 'premium', 'discount', 'equilibrium'
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'side': self.side,
            'price': self.price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'confidence': self.confidence,
            'signal_type': self.signal_type,
            'market_structure': self.market_structure,
            'order_blocks': self.order_blocks,
            'fvgs': self.fvgs,
            'swing_points': self.swing_points,
            'liquidity_levels': self.liquidity_levels,
            'atr': self.atr,
            'volatility_regime': self.volatility_regime,
            'premium_discount': self.premium_discount,
        }


class SMCDetector:
    """
    Smart Money Concepts detector
    
    Parameters:
        swing_length: Number of bars for swing detection (default: 5)
        ob_lookback: Bars to look back for Order Blocks (default: 20)
        fvg_lookback: Bars to look back for FVGs (default: 50)
        atr_period: ATR period for volatility filter (default: 14)
        atr_multiplier: Multiplier for SL/TP calculation (default: 1.5)
    """
    
    def __init__(self, 
                 swing_length: int = 5,
                 ob_lookback: int = 20,
                 fvg_lookback: int = 50,
                 atr_period: int = 14,
                 atr_multiplier: float = 1.5):
        self.swing_length = swing_length
        self.ob_lookback = ob_lookback
        self.fvg_lookback = fvg_lookback
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
    
    def detect_swings(self, df: pd.DataFrame) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """
        Detect swing highs and swing lows
        
        Returns:
            Tuple of (swing_highs, swing_lows)
        """
        swing_highs = []
        swing_lows = []
        
        for i in range(self.swing_length, len(df) - self.swing_length):
            # Check swing high
            current_high = df['high'].iloc[i]
            left_highs = df['high'].iloc[i-self.swing_length:i]
            right_highs = df['high'].iloc[i+1:i+self.swing_length+1]
            
            if (current_high > left_highs.max()) and (current_high > right_highs.max()):
                swing_highs.append(SwingPoint(
                    index=i,
                    timestamp=df.index[i],
                    price=current_high,
                    type='high'
                ))
            
            # Check swing low
            current_low = df['low'].iloc[i]
            left_lows = df['low'].iloc[i-self.swing_length:i]
            right_lows = df['low'].iloc[i+1:i+self.swing_length+1]
            
            if (current_low < left_lows.min()) and (current_low < right_lows.min()):
                swing_lows.append(SwingPoint(
                    index=i,
                    timestamp=df.index[i],
                    price=current_low,
                    type='low'
                ))
        
        return swing_highs, swing_lows
    
    def detect_bos_choch(self, df: pd.DataFrame, swing_highs: List[SwingPoint], 
                        swing_lows: List[SwingPoint]) -> List[Dict]:
        """
        Detect Break of Structure (BOS) and Change of Character (CHoCH)
        
        Returns:
            List of structure break events
        """
        breaks = []
        
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return breaks
        
        # Check for bullish BOS (break above previous swing high)
        for i, high in enumerate(swing_highs[:-1]):
            next_high = swing_highs[i + 1]
            
            # Find closes above this swing high
            mask = (df.index > high.timestamp) & (df.index <= next_high.timestamp)
            closes_above = df.loc[mask, 'close'] > high.price
            
            if closes_above.any():
                first_break_idx = closes_above.idxmax()
                breaks.append({
                    'type': 'BOS',
                    'direction': 'bullish',
                    'timestamp': first_break_idx,
                    'price': high.price,
                    'break_price': df.loc[first_break_idx, 'close'],
                })
        
        # Check for bearish BOS (break below previous swing low)
        for i, low in enumerate(swing_lows[:-1]):
            next_low = swing_lows[i + 1]
            
            mask = (df.index > low.timestamp) & (df.index <= next_low.timestamp)
            closes_below = df.loc[mask, 'close'] < low.price
            
            if closes_below.any():
                first_break_idx = closes_below.idxmax()
                breaks.append({
                    'type': 'BOS',
                    'direction': 'bearish',
                    'timestamp': first_break_idx,
                    'price': low.price,
                    'break_price': df.loc[first_break_idx, 'close'],
                })
        
        return breaks
    
    def detect_order_blocks(self, df: pd.DataFrame) -> List[OrderBlock]:
        """
        Detect Order Blocks (last down candle before strong up move, or vice versa)
        
        Returns:
            List of OrderBlock objects
        """
        order_blocks = []
        
        for i in range(1, len(df) - 1):
            current = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Bullish OB: last bearish candle before bullish impulse
            if current['close'] < current['open']:  # Bearish candle
                # Check if next candle is strong bullish
                next_body = next_candle['close'] - next_candle['open']
                current_body = current['open'] - current['close']
                
                if next_body > 0 and next_body > current_body * 2:  # Strong bullish move
                    ob = OrderBlock(
                        start_index=i,
                        end_index=i,
                        start_time=df.index[i],
                        end_time=df.index[i],
                        high=current['high'],
                        low=current['low'],
                        type='bullish',
                        strength=min(100, (next_body / current_body) * 20)
                    )
                    order_blocks.append(ob)
            
            # Bearish OB: last bullish candle before bearish impulse
            elif current['close'] > current['open']:  # Bullish candle
                next_body = next_candle['open'] - next_candle['close']
                current_body = current['close'] - current['open']
                
                if next_body > 0 and next_body > current_body * 2:  # Strong bearish move
                    ob = OrderBlock(
                        start_index=i,
                        end_index=i,
                        start_time=df.index[i],
                        end_time=df.index[i],
                        high=current['high'],
                        low=current['low'],
                        type='bearish',
                        strength=min(100, (next_body / current_body) * 20)
                    )
                    order_blocks.append(ob)
        
        return order_blocks
    
    def detect_fvg(self, df: pd.DataFrame) -> List[FairValueGap]:
        """
        Detect Fair Value Gaps (gaps in price action that haven't been filled)
        
        Returns:
            List of FairValueGap objects
        """
        fvgs = []
        
        for i in range(1, len(df) - 1):
            prev_candle = df.iloc[i - 1]
            current = df.iloc[i]
            next_candle = df.iloc[i + 1]
            
            # Bullish FVG: gap between prev high and next low
            if prev_candle['high'] < next_candle['low']:
                fvg = FairValueGap(
                    index=i,
                    timestamp=df.index[i],
                    top=next_candle['low'],
                    bottom=prev_candle['high'],
                    type='bullish'
                )
                fvgs.append(fvg)
            
            # Bearish FVG: gap between prev low and next high
            elif prev_candle['low'] > next_candle['high']:
                fvg = FairValueGap(
                    index=i,
                    timestamp=df.index[i],
                    top=prev_candle['low'],
                    bottom=next_candle['high'],
                    type='bearish'
                )
                fvgs.append(fvg)
        
        return fvgs
    
    def detect_liquidity_sweeps(self, df: pd.DataFrame, swing_highs: List[SwingPoint],
                               swing_lows: List[SwingPoint]) -> List[Dict]:
        """
        Detect liquidity sweeps (wick through swing point then reversal)
        
        Returns:
            List of liquidity sweep events
        """
        sweeps = []
        
        # Check for liquidity grab above swing highs
        for high in swing_highs:
            # Look for wicks above this high in subsequent bars
            mask = df.index > high.timestamp
            future_bars = df.loc[mask]
            
            for idx in future_bars.index[:20]:  # Check next 20 bars
                bar = future_bars.loc[idx]
                
                # Wick above high but close below
                if bar['high'] > high.price and bar['close'] < high.price:
                    sweeps.append({
                        'type': 'liquidity_sweep',
                        'direction': 'bearish',
                        'timestamp': idx,
                        'level': high.price,
                        'wick_high': bar['high'],
                        'close': bar['close'],
                    })
                    break
        
        # Check for liquidity grab below swing lows
        for low in swing_lows:
            mask = df.index > low.timestamp
            future_bars = df.loc[mask]
            
            for idx in future_bars.index[:20]:
                bar = future_bars.loc[idx]
                
                # Wick below low but close above
                if bar['low'] < low.price and bar['close'] > low.price:
                    sweeps.append({
                        'type': 'liquidity_sweep',
                        'direction': 'bullish',
                        'timestamp': idx,
                        'level': low.price,
                        'wick_low': bar['low'],
                        'close': bar['close'],
                    })
                    break
        
        return sweeps
    
    def calculate_premium_discount(self, df: pd.DataFrame, swing_highs: List[SwingPoint],
                                   swing_lows: List[SwingPoint]) -> str:
        """
        Determine if price is in premium, discount, or equilibrium zone
        
        Returns:
            'premium', 'discount', or 'equilibrium'
        """
        if not swing_highs or not swing_lows:
            return 'equilibrium'
        
        recent_high = max(swing_highs, key=lambda x: x.timestamp).price
        recent_low = min(swing_lows, key=lambda x: x.timestamp).price
        current_price = df['close'].iloc[-1]
        
        range_size = recent_high - recent_low
        position = (current_price - recent_low) / range_size if range_size > 0 else 0.5
        
        if position > 0.62:  # Above 62% (premium zone)
            return 'premium'
        elif position < 0.38:  # Below 38% (discount zone)
            return 'discount'
        else:
            return 'equilibrium'
    
    def detect_smc_signals(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[SMCSignal]:
        """
        Main detection method - analyzes dataframe and returns SMC signals
        
        Args:
            df: DataFrame with OHLCV data and datetime index
            symbol: Trading symbol
            timeframe: Timeframe string
        
        Returns:
            List of SMCSignal objects
        """
        signals = []
        
        # Calculate ATR for volatility
        from .indicators import atr as calc_atr
        atr_values = calc_atr(df, self.atr_period)
        current_atr = atr_values.iloc[-1]
        
        # Detect all SMC components
        swing_highs, swing_lows = self.detect_swings(df)
        order_blocks = self.detect_order_blocks(df)
        fvgs = self.detect_fvg(df)
        bos_choch = self.detect_bos_choch(df, swing_highs, swing_lows)
        liquidity_sweeps = self.detect_liquidity_sweeps(df, swing_highs, swing_lows)
        premium_discount = self.calculate_premium_discount(df, swing_highs, swing_lows)
        
        # Determine market structure
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            recent_highs = sorted(swing_highs, key=lambda x: x.timestamp)[-2:]
            recent_lows = sorted(swing_lows, key=lambda x: x.timestamp)[-2:]
            
            hh = recent_highs[1].price > recent_highs[0].price
            hl = recent_lows[1].price > recent_lows[0].price
            lh = recent_highs[1].price < recent_highs[0].price
            ll = recent_lows[1].price < recent_lows[0].price
            
            if hh and hl:
                market_structure = 'bullish'
            elif lh and ll:
                market_structure = 'bearish'
            else:
                market_structure = 'ranging'
        else:
            market_structure = 'ranging'
        
        # Generate signals based on Order Block retests
        current_price = df['close'].iloc[-1]
        current_time = df.index[-1]
        
        for ob in order_blocks[-self.ob_lookback:]:  # Check recent OBs
            # Bullish OB retest in discount zone
            if (ob.type == 'bullish' and 
                premium_discount == 'discount' and
                market_structure != 'bearish'):
                
                # Check if price is near OB
                if ob.low <= current_price <= ob.high * 1.02:  # Within 2% of OB
                    signal = SMCSignal(
                        timestamp=current_time,
                        symbol=symbol,
                        timeframe=timeframe,
                        side='buy',
                        price=current_price,
                        stop_loss=ob.low - (current_atr * self.atr_multiplier),
                        take_profit=current_price + (current_atr * self.atr_multiplier * 2),
                        confidence=min(95, 60 + ob.strength / 3),
                        signal_type='ob_retest',
                        market_structure=market_structure,
                        order_blocks=[{'type': ob.type, 'high': ob.high, 'low': ob.low, 'strength': ob.strength}],
                        fvgs=[{'type': fvg.type, 'top': fvg.top, 'bottom': fvg.bottom} for fvg in fvgs[-5:]],
                        swing_points=[{'type': 'high', 'price': sh.price} for sh in swing_highs[-3:]] + 
                                    [{'type': 'low', 'price': sl.price} for sl in swing_lows[-3:]],
                        liquidity_levels=[ls for ls in liquidity_sweeps[-5:]],
                        atr=float(current_atr),
                        volatility_regime='normal',
                        premium_discount=premium_discount
                    )
                    signals.append(signal)
            
            # Bearish OB retest in premium zone
            elif (ob.type == 'bearish' and 
                  premium_discount == 'premium' and
                  market_structure != 'bullish'):
                
                if ob.low * 0.98 <= current_price <= ob.high:  # Within 2% of OB
                    signal = SMCSignal(
                        timestamp=current_time,
                        symbol=symbol,
                        timeframe=timeframe,
                        side='sell',
                        price=current_price,
                        stop_loss=ob.high + (current_atr * self.atr_multiplier),
                        take_profit=current_price - (current_atr * self.atr_multiplier * 2),
                        confidence=min(95, 60 + ob.strength / 3),
                        signal_type='ob_retest',
                        market_structure=market_structure,
                        order_blocks=[{'type': ob.type, 'high': ob.high, 'low': ob.low, 'strength': ob.strength}],
                        fvgs=[{'type': fvg.type, 'top': fvg.top, 'bottom': fvg.bottom} for fvg in fvgs[-5:]],
                        swing_points=[{'type': 'high', 'price': sh.price} for sh in swing_highs[-3:]] + 
                                    [{'type': 'low', 'price': sl.price} for sl in swing_lows[-3:]],
                        liquidity_levels=[ls for ls in liquidity_sweeps[-5:]],
                        atr=float(current_atr),
                        volatility_regime='normal',
                        premium_discount=premium_discount
                    )
                    signals.append(signal)
        
        return signals


def detect_smc(df: pd.DataFrame, symbol: str, timeframe: str, **kwargs) -> List[Dict]:
    """
    Convenience function for SMC detection
    
    Args:
        df: DataFrame with OHLCV data
        symbol: Trading symbol
        timeframe: Timeframe string
        **kwargs: Additional parameters for SMCDetector
    
    Returns:
        List of signal dictionaries
    """
    detector = SMCDetector(**kwargs)
    signals = detector.detect_smc_signals(df, symbol, timeframe)
    return [signal.to_dict() for signal in signals]
