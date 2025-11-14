"""
Historical Market Data Fetcher

Fetches historical OHLCV data using free data sources:
- Primary: yfinance (Yahoo Finance) - Free, no API key required
- Fallback: Alpha Vantage (requires free API key)
- Support for Forex, Crypto, Stocks, Indices

No paid APIs required.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
import logging
import time

logger = logging.getLogger(__name__)


class HistoricalDataFetcher:
    """
    Unified interface for fetching historical market data
    """
    
    def __init__(self, source: str = 'yfinance', api_key: Optional[str] = None):
        """
        Initialize data fetcher
        
        Args:
            source: Data source ('yfinance', 'alphavantage')
            api_key: API key for Alpha Vantage (optional)
        """
        self.source = source
        self.api_key = api_key
    
    def normalize_symbol(self, symbol: str, source: str) -> str:
        """
        Normalize symbol format for different data sources
        
        Args:
            symbol: Raw symbol (e.g., 'EURUSD', 'BTCUSD')
            source: Data source name
        
        Returns:
            Normalized symbol for the source
        """
        symbol = symbol.upper().strip()
        
        if source == 'yfinance':
            # Forex pairs: EURUSD -> EURUSD=X
            if len(symbol) == 6 and symbol.isalpha():
                return f"{symbol}=X"
            # Crypto: BTCUSD -> BTC-USD
            if 'BTC' in symbol or 'ETH' in symbol:
                base = symbol[:3]
                quote = symbol[3:]
                return f"{base}-{quote}"
            # Stocks/indices remain as is
            return symbol
        
        elif source == 'alphavantage':
            # Alpha Vantage forex format
            if len(symbol) == 6 and symbol.isalpha():
                return symbol  # Already in correct format
            return symbol
        
        return symbol
    
    def normalize_timeframe(self, timeframe: str) -> tuple:
        """
        Normalize timeframe to (interval, period) for data sources
        
        Args:
            timeframe: Timeframe string (1, 5, 15, 30, 1H, 4H, D, W, M)
        
        Returns:
            Tuple of (interval_string, lookback_period)
        """
        tf_map = {
            '1': ('1m', '7d'),
            '5': ('5m', '60d'),
            '15': ('15m', '60d'),
            '30': ('30m', '60d'),
            '1H': ('1h', '730d'),
            '4H': ('1h', '730d'),  # Will resample
            'D': ('1d', '5y'),
            'W': ('1wk', '10y'),
            'M': ('1mo', '20y'),
        }
        return tf_map.get(timeframe, ('1h', '730d'))
    
    def fetch_yfinance(self, symbol: str, timeframe: str, 
                       start: Optional[datetime] = None, 
                       end: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch data from Yahoo Finance (yfinance)
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start: Start date
            end: End date
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            import yfinance as yf
        except ImportError:
            logger.error("yfinance not installed. Run: pip install yfinance")
            return pd.DataFrame()
        
        # Normalize symbol
        ticker_symbol = self.normalize_symbol(symbol, 'yfinance')
        interval, period = self.normalize_timeframe(timeframe)
        
        logger.info(f"Fetching {ticker_symbol} {interval} from yfinance...")
        
        # Create ticker object
        ticker = yf.Ticker(ticker_symbol)
        
        # Fetch data
        if start and end:
            df = ticker.history(start=start, end=end, interval=interval)
        else:
            df = ticker.history(period=period, interval=interval)
        
        if df.empty:
            logger.warning(f"No data returned for {ticker_symbol}")
            return pd.DataFrame()
        
        # Standardize column names
        df = df.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })
        
        # Keep only OHLCV columns
        df = df[['open', 'high', 'low', 'close', 'volume']]
        
        # Resample if needed (e.g., 4H from 1H data)
        if timeframe == '4H' and interval == '1h':
            df = self.resample_dataframe(df, '4H')
        
        # Reset index to make timestamp a column
        df = df.reset_index()
        df = df.rename(columns={'Date': 'timestamp', 'Datetime': 'timestamp'})
        
        # Ensure timestamp is datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        logger.info(f"Fetched {len(df)} bars for {symbol}")
        return df
    
    def fetch_alphavantage(self, symbol: str, timeframe: str,
                          start: Optional[datetime] = None,
                          end: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch data from Alpha Vantage (requires API key)
        
        Note: Free tier has limitations (5 requests/minute, 500/day)
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start: Start date
            end: End date
        
        Returns:
            DataFrame with OHLCV data
        """
        if not self.api_key:
            logger.error("Alpha Vantage API key required")
            return pd.DataFrame()
        
        try:
            import requests
        except ImportError:
            logger.error("requests not installed. Run: pip install requests")
            return pd.DataFrame()
        
        base_url = "https://www.alphavantage.co/query"
        
        # Determine function based on timeframe
        if timeframe in ['1', '5', '15', '30']:
            function = 'FX_INTRADAY'
            interval_map = {'1': '1min', '5': '5min', '15': '15min', '30': '30min'}
            interval = interval_map[timeframe]
        elif timeframe in ['1H', '4H']:
            function = 'FX_INTRADAY'
            interval = '60min'
        else:
            function = 'FX_DAILY'
            interval = None
        
        # Build parameters
        params = {
            'function': function,
            'from_symbol': symbol[:3],
            'to_symbol': symbol[3:],
            'apikey': self.api_key,
            'outputsize': 'full'
        }
        
        if interval:
            params['interval'] = interval
        
        logger.info(f"Fetching {symbol} from Alpha Vantage...")
        
        response = requests.get(base_url, params=params)
        data = response.json()
        
        # Parse response
        if 'Error Message' in data:
            logger.error(f"Alpha Vantage error: {data['Error Message']}")
            return pd.DataFrame()
        
        # Find time series key
        ts_key = None
        for key in data.keys():
            if 'Time Series' in key:
                ts_key = key
                break
        
        if not ts_key:
            logger.error("No time series data in response")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame.from_dict(data[ts_key], orient='index')
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        
        # Standardize column names
        df.columns = ['open', 'high', 'low', 'close', 'volume']
        df = df.astype(float)
        
        # Filter by date range if provided
        if start:
            df = df[df.index >= start]
        if end:
            df = df[df.index <= end]
        
        df = df.reset_index()
        df = df.rename(columns={'index': 'timestamp'})
        
        logger.info(f"Fetched {len(df)} bars for {symbol}")
        
        # Rate limiting
        time.sleep(12)  # Free tier: max 5 requests/minute
        
        return df
    
    def resample_dataframe(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Resample DataFrame to different timeframe
        
        Args:
            df: DataFrame with OHLCV data and datetime index
            timeframe: Target timeframe
        
        Returns:
            Resampled DataFrame
        """
        if 'timestamp' in df.columns:
            df = df.set_index('timestamp')
        
        # Resample rules
        resample_rules = {
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }
        
        # Map timeframe to pandas offset
        offset_map = {
            '4H': '4H',
            'D': '1D',
            'W': '1W',
            'M': '1M'
        }
        
        offset = offset_map.get(timeframe, '1H')
        resampled = df.resample(offset).agg(resample_rules).dropna()
        
        return resampled
    
    def get_candles(self, symbol: str, timeframe: str,
                   start: Optional[datetime] = None,
                   end: Optional[datetime] = None,
                   max_retries: int = 3) -> pd.DataFrame:
        """
        Main method to fetch candles with automatic fallback
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe string
            start: Start date (optional)
            end: End date (optional)
            max_retries: Maximum retry attempts
        
        Returns:
            DataFrame with OHLCV data
        """
        for attempt in range(max_retries):
            try:
                if self.source == 'yfinance':
                    df = self.fetch_yfinance(symbol, timeframe, start, end)
                    if not df.empty:
                        return df
                    
                    # Try alphavantage as fallback
                    if self.api_key:
                        logger.info("Trying Alpha Vantage as fallback...")
                        df = self.fetch_alphavantage(symbol, timeframe, start, end)
                        if not df.empty:
                            return df
                
                elif self.source == 'alphavantage':
                    df = self.fetch_alphavantage(symbol, timeframe, start, end)
                    if not df.empty:
                        return df
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        logger.error(f"Failed to fetch data for {symbol} after {max_retries} attempts")
        return pd.DataFrame()
    
    def save_to_csv(self, df: pd.DataFrame, symbol: str, timeframe: str, 
                   output_dir: str = 'adapters/sample_data') -> str:
        """
        Save DataFrame to CSV file
        
        Args:
            df: DataFrame to save
            symbol: Trading symbol
            timeframe: Timeframe string
            output_dir: Output directory
        
        Returns:
            Path to saved file
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"{symbol.lower()}_{timeframe.lower()}.csv"
        filepath = os.path.join(output_dir, filename)
        
        df.to_csv(filepath, index=False)
        logger.info(f"Saved {len(df)} bars to {filepath}")
        
        return filepath
    
    def load_from_csv(self, filepath: str) -> pd.DataFrame:
        """
        Load DataFrame from CSV file
        
        Args:
            filepath: Path to CSV file
        
        Returns:
            DataFrame with OHLCV data
        """
        df = pd.read_csv(filepath, parse_dates=['timestamp'])
        return df


# Convenience functions

def fetch_historical_data(symbol: str, timeframe: str,
                         start: Optional[datetime] = None,
                         end: Optional[datetime] = None,
                         source: str = 'yfinance',
                         api_key: Optional[str] = None) -> pd.DataFrame:
    """
    Convenience function to fetch historical data
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe string
        start: Start date
        end: End date
        source: Data source
        api_key: API key for paid sources
    
    Returns:
        DataFrame with OHLCV data
    """
    fetcher = HistoricalDataFetcher(source=source, api_key=api_key)
    return fetcher.get_candles(symbol, timeframe, start, end)


def generate_sample_data(symbols: List[str] = None, 
                        timeframes: List[str] = None,
                        output_dir: str = 'adapters/sample_data'):
    """
    Generate sample data files for testing
    
    Args:
        symbols: List of symbols to fetch
        timeframes: List of timeframes to fetch
        output_dir: Output directory for CSV files
    """
    if symbols is None:
        symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD', 'BTCUSD', 
                  'ETHUSD', 'AAPL', 'TSLA', 'SPY', 'QQQ']
    
    if timeframes is None:
        timeframes = ['1H', '4H', 'D']
    
    fetcher = HistoricalDataFetcher(source='yfinance')
    
    for symbol in symbols:
        for timeframe in timeframes:
            try:
                logger.info(f"Fetching {symbol} {timeframe}...")
                df = fetcher.get_candles(symbol, timeframe)
                
                if not df.empty:
                    # Keep last 1000 bars for sample data
                    df = df.tail(1000)
                    fetcher.save_to_csv(df, symbol, timeframe, output_dir)
                
                time.sleep(1)  # Rate limiting
            
            except Exception as e:
                logger.error(f"Error fetching {symbol} {timeframe}: {e}")
                continue


if __name__ == '__main__':
    # Test script
    logging.basicConfig(level=logging.INFO)
    
    # Fetch sample data
    print("Fetching EURUSD 1H data...")
    df = fetch_historical_data('EURUSD', '1H')
    print(f"Fetched {len(df)} bars")
    print(df.head())
    print(df.tail())
    
    # Generate all sample data (uncomment to run)
    # print("\nGenerating sample data for all symbols...")
    # generate_sample_data()
