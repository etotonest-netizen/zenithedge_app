"""
Technical Indicators Library

Vectorized technical indicators using pandas and numpy for efficient computation.
All functions operate on DataFrames with OHLCV columns.

Functions:
- ATR: Average True Range
- SMA/EMA: Simple/Exponential Moving Averages
- Stdev: Standard Deviation
- ADX: Average Directional Index
- VWAP: Volume Weighted Average Price
- RSI: Relative Strength Index
- Bollinger Bands
- Keltner Channels
"""

import pandas as pd
import numpy as np
from typing import Union, Tuple


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR)
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ATR period (default: 14)
    
    Returns:
        Series with ATR values
    """
    high = df['high']
    low = df['low']
    close = df['close']
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """
    Simple Moving Average
    
    Args:
        series: Price series
        period: SMA period
    
    Returns:
        Series with SMA values
    """
    return series.rolling(window=period).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average
    
    Args:
        series: Price series
        period: EMA period
    
    Returns:
        Series with EMA values
    """
    return series.ewm(span=period, adjust=False).mean()


def stdev(series: pd.Series, period: int) -> pd.Series:
    """
    Standard Deviation
    
    Args:
        series: Price series
        period: Period for std calculation
    
    Returns:
        Series with standard deviation values
    """
    return series.rolling(window=period).std()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index
    
    Args:
        series: Price series (typically close)
        period: RSI period (default: 14)
    
    Returns:
        Series with RSI values (0-100)
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.ewm(span=period, adjust=False).mean()
    avg_loss = loss.ewm(span=period, adjust=False).mean()
    
    rs = avg_gain / avg_loss
    rsi_values = 100 - (100 / (1 + rs))
    
    return rsi_values


def bollinger_bands(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands
    
    Args:
        df: DataFrame with 'close' column
        period: MA period (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)
    
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    close = df['close']
    middle = sma(close, period)
    std = stdev(close, period)
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def keltner_channels(df: pd.DataFrame, period: int = 20, atr_multiplier: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Keltner Channels
    
    Args:
        df: DataFrame with OHLC columns
        period: MA period (default: 20)
        atr_multiplier: ATR multiplier (default: 2.0)
    
    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    close = df['close']
    middle = ema(close, period)
    atr_values = atr(df, period)
    
    upper = middle + (atr_values * atr_multiplier)
    lower = middle - (atr_values * atr_multiplier)
    
    return upper, middle, lower


def adx(df: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Average Directional Index (ADX) with +DI and -DI
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
        period: ADX period (default: 14)
    
    Returns:
        Tuple of (adx, plus_di, minus_di)
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # Calculate +DM and -DM
    high_diff = high.diff()
    low_diff = -low.diff()
    
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    # Calculate ATR
    atr_values = atr(df, period)
    
    # Calculate +DI and -DI
    plus_di = 100 * (plus_dm.ewm(span=period, adjust=False).mean() / atr_values)
    minus_di = 100 * (minus_dm.ewm(span=period, adjust=False).mean() / atr_values)
    
    # Calculate DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx_values = dx.ewm(span=period, adjust=False).mean()
    
    return adx_values, plus_di, minus_di


def vwap(df: pd.DataFrame, session_start: str = '00:00') -> pd.Series:
    """
    Volume Weighted Average Price
    
    Calculates VWAP from session start (resets daily by default)
    
    Args:
        df: DataFrame with 'high', 'low', 'close', 'volume' columns and DateTimeIndex
        session_start: Session start time (default: '00:00' for daily reset)
    
    Returns:
        Series with VWAP values
    """
    # Typical price
    typical_price = (df['high'] + df['low'] + df['close']) / 3
    
    # Volume * Typical Price
    vwap_values = (typical_price * df['volume']).cumsum() / df['volume'].cumsum()
    
    # Reset at session start (daily for forex/crypto)
    if hasattr(df.index, 'date'):
        # Group by date and calculate cumulative VWAP
        df_copy = df.copy()
        df_copy['typical_price'] = typical_price
        df_copy['vp'] = typical_price * df['volume']
        
        grouped = df_copy.groupby(df_copy.index.date)
        vwap_values = grouped['vp'].cumsum() / grouped['volume'].cumsum()
    
    return vwap_values


def swing_highs_lows(df: pd.DataFrame, left_bars: int = 5, right_bars: int = 5) -> Tuple[pd.Series, pd.Series]:
    """
    Detect swing highs and swing lows
    
    A swing high is a high that is higher than N bars to the left and right.
    A swing low is a low that is lower than N bars to the left and right.
    
    Args:
        df: DataFrame with 'high' and 'low' columns
        left_bars: Number of bars to check on the left (default: 5)
        right_bars: Number of bars to check on the right (default: 5)
    
    Returns:
        Tuple of (swing_highs, swing_lows) as boolean Series
    """
    high = df['high']
    low = df['low']
    
    # Initialize result series
    swing_highs = pd.Series(False, index=df.index)
    swing_lows = pd.Series(False, index=df.index)
    
    # Check each bar (skip first/last bars where we don't have enough context)
    for i in range(left_bars, len(df) - right_bars):
        # Check if current high is swing high
        current_high = high.iloc[i]
        left_highs = high.iloc[i-left_bars:i]
        right_highs = high.iloc[i+1:i+right_bars+1]
        
        if (current_high > left_highs.max()) and (current_high > right_highs.max()):
            swing_highs.iloc[i] = True
        
        # Check if current low is swing low
        current_low = low.iloc[i]
        left_lows = low.iloc[i-left_bars:i]
        right_lows = low.iloc[i+1:i+right_bars+1]
        
        if (current_low < left_lows.min()) and (current_low < right_lows.min()):
            swing_lows.iloc[i] = True
    
    return swing_highs, swing_lows


def pivot_points(df: pd.DataFrame) -> dict:
    """
    Calculate classic pivot points (PP, R1, R2, R3, S1, S2, S3)
    
    Args:
        df: DataFrame with 'high', 'low', 'close' columns
    
    Returns:
        Dictionary with pivot levels
    """
    high = df['high'].iloc[-1]
    low = df['low'].iloc[-1]
    close = df['close'].iloc[-1]
    
    pp = (high + low + close) / 3
    
    r1 = 2 * pp - low
    r2 = pp + (high - low)
    r3 = high + 2 * (pp - low)
    
    s1 = 2 * pp - high
    s2 = pp - (high - low)
    s3 = low - 2 * (high - pp)
    
    return {
        'pp': pp,
        'r1': r1, 'r2': r2, 'r3': r3,
        's1': s1, 's2': s2, 's3': s3,
    }


def market_structure(df: pd.DataFrame, swing_period: int = 5) -> dict:
    """
    Analyze market structure (Higher Highs, Higher Lows, etc.)
    
    Args:
        df: DataFrame with OHLC data
        swing_period: Period for swing detection
    
    Returns:
        Dictionary with market structure analysis
    """
    swing_highs_mask, swing_lows_mask = swing_highs_lows(df, swing_period, swing_period)
    
    # Get swing high/low values
    swing_high_values = df.loc[swing_highs_mask, 'high']
    swing_low_values = df.loc[swing_lows_mask, 'low']
    
    if len(swing_high_values) < 2 or len(swing_low_values) < 2:
        return {
            'trend': 'undefined',
            'last_swing_high': None,
            'last_swing_low': None,
        }
    
    # Check for HH/HL (uptrend) or LH/LL (downtrend)
    recent_highs = swing_high_values.tail(2).values
    recent_lows = swing_low_values.tail(2).values
    
    hh = recent_highs[-1] > recent_highs[-2]  # Higher High
    hl = recent_lows[-1] > recent_lows[-2]    # Higher Low
    lh = recent_highs[-1] < recent_highs[-2]  # Lower High
    ll = recent_lows[-1] < recent_lows[-2]    # Lower Low
    
    if hh and hl:
        trend = 'uptrend'
    elif lh and ll:
        trend = 'downtrend'
    else:
        trend = 'ranging'
    
    return {
        'trend': trend,
        'last_swing_high': float(swing_high_values.iloc[-1]),
        'last_swing_low': float(swing_low_values.iloc[-1]),
        'swing_high_times': swing_high_values.index.tolist(),
        'swing_low_times': swing_low_values.index.tolist(),
    }


def calculate_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate all indicators and add them as columns to DataFrame
    
    Args:
        df: DataFrame with OHLCV data
    
    Returns:
        DataFrame with all indicator columns added
    """
    df = df.copy()
    
    # Moving averages
    df['sma_20'] = sma(df['close'], 20)
    df['sma_50'] = sma(df['close'], 50)
    df['sma_200'] = sma(df['close'], 200)
    df['ema_9'] = ema(df['close'], 9)
    df['ema_21'] = ema(df['close'], 21)
    df['ema_50'] = ema(df['close'], 50)
    
    # ATR
    df['atr_14'] = atr(df, 14)
    
    # RSI
    df['rsi_14'] = rsi(df['close'], 14)
    df['rsi_3'] = rsi(df['close'], 3)  # For scalping
    
    # Bollinger Bands
    bb_upper, bb_middle, bb_lower = bollinger_bands(df, 20, 2.0)
    df['bb_upper'] = bb_upper
    df['bb_middle'] = bb_middle
    df['bb_lower'] = bb_lower
    
    # Keltner Channels
    kc_upper, kc_middle, kc_lower = keltner_channels(df, 20, 2.0)
    df['kc_upper'] = kc_upper
    df['kc_middle'] = kc_middle
    df['kc_lower'] = kc_lower
    
    # ADX
    adx_values, plus_di, minus_di = adx(df, 14)
    df['adx'] = adx_values
    df['plus_di'] = plus_di
    df['minus_di'] = minus_di
    
    # VWAP
    if 'volume' in df.columns:
        df['vwap'] = vwap(df)
    
    return df


# Helper functions for common calculations

def calculate_pips(entry: float, exit: float, symbol: str) -> float:
    """
    Calculate pip difference between two prices
    
    Args:
        entry: Entry price
        exit: Exit price
        symbol: Trading symbol (to determine pip value)
    
    Returns:
        Pip difference
    """
    # For JPY pairs, 1 pip = 0.01, for others 1 pip = 0.0001
    if 'JPY' in symbol.upper():
        pip_value = 0.01
    else:
        pip_value = 0.0001
    
    return abs(exit - entry) / pip_value


def normalize_timeframe(tf: str) -> str:
    """
    Normalize timeframe string to consistent format
    
    Args:
        tf: Timeframe string (various formats)
    
    Returns:
        Normalized timeframe (1, 5, 15, 30, 1H, 4H, D, W, M)
    """
    tf = tf.upper().strip()
    
    # Map common variations
    mapping = {
        '1M': '1', '1MIN': '1',
        '5M': '5', '5MIN': '5',
        '15M': '15', '15MIN': '15',
        '30M': '30', '30MIN': '30',
        '60': '1H', '60M': '1H', '60MIN': '1H', 'H1': '1H',
        '240': '4H', '240M': '4H', '4HOUR': '4H', 'H4': '4H',
        '1D': 'D', 'DAILY': 'D', 'DAY': 'D',
        '1W': 'W', 'WEEKLY': 'W', 'WEEK': 'W',
        '1MO': 'M', 'MONTHLY': 'M', 'MONTH': 'M',
    }
    
    return mapping.get(tf, tf)
