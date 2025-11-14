"""
Deterministic Replay Engine

Replays OHLCV candles around insight timeframe and re-validates
technical patterns to verify detector accuracy.
"""
import logging
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)


class OHLCVReplay:
    """
    Deterministic candle replay system
    
    Fetches and caches OHLCV data for reproducible audits
    """
    
    def __init__(self, insight, horizon_delta: timedelta):
        """
        Initialize replay for an insight
        
        Args:
            insight: Signal model instance
            horizon_delta: Time period to fetch (e.g., timedelta(hours=4))
        """
        self.insight = insight
        self.symbol = insight.symbol
        self.horizon_delta = horizon_delta
        self.candles = []
        self.metadata = {}
        
        # Calculate time range for fetching
        self.start_time = insight.received_at
        self.end_time = self.start_time + horizon_delta
    
    def fetch_candles(self, from_dt, to_dt):
        """
        Fetch historical OHLCV candles from database.
        
        Queries the marketdata.OHLCVCandle model for 1-minute candles
        in the specified time range. These are used to build higher
        timeframe OHLCV data for outcome evaluation.
        """
        try:
            from marketdata.models import OHLCVCandle
            
            # Fetch 1-minute candles (finest granularity)
            candles = OHLCVCandle.objects.filter(
                symbol=self.symbol,
                timeframe='1m',
                timestamp__gte=from_dt,
                timestamp__lte=to_dt
            ).order_by('timestamp').values(
                'timestamp', 'open_price', 'high', 'low', 'close', 'volume'
            )
            
            if not candles:
                print(f"No candles found for {self.symbol} {from_dt} to {to_dt}")
                return None
            
            # Convert to list of dicts for processing
            return [
                {
                    'timestamp': c['timestamp'],
                    'open': float(c['open_price']),
                    'high': float(c['high']),
                    'low': float(c['low']),
                    'close': float(c['close']),
                    'volume': float(c['volume']) if c['volume'] else 0
                }
                for c in candles
            ]
            
        except ImportError:
            print(f"⚠️  marketdata app not available, cannot fetch candles")
            return None
        except Exception as e:
            print(f"Error fetching candles: {e}")
            return None
    
    def _fetch_from_database(self, start_time, end_time) -> List[Dict]:
        """Fetch candles from local database"""
        try:
            # Check if we have a MarketData or similar model
            from signals.models import MarketData  # Adjust import as needed
            
            data = MarketData.objects.filter(
                symbol=self.insight.symbol,
                timeframe=self.insight.timeframe,
                timestamp__gte=start_time,
                timestamp__lte=end_time
            ).order_by('timestamp')
            
            candles = []
            for d in data:
                candles.append({
                    'timestamp': d.timestamp,
                    'open': float(d.open),
                    'high': float(d.high),
                    'low': float(d.low),
                    'close': float(d.close),
                    'volume': float(d.volume) if hasattr(d, 'volume') else 0
                })
            
            return candles
        
        except ImportError:
            logger.debug("MarketData model not available")
            return []
        except Exception as e:
            logger.error(f"Database fetch error: {e}")
            return []
    
    def _fetch_from_broker(self, broker_api, start_time, end_time) -> List[Dict]:
        """Fetch candles from broker API"""
        try:
            # Placeholder for broker API integration
            # Would call broker_api.get_historical_data(...)
            logger.warning("Broker API integration not implemented")
            return []
        except Exception as e:
            logger.error(f"Broker API fetch error: {e}")
            return []
    
    def get_aggregated_ohlcv(self) -> Dict:
        """
        Aggregate all candles into single OHLCV bar
        
        Returns:
            Dictionary with aggregated high/low/close
        """
        if not self.candles:
            return {}
        
        try:
            high = max(c['high'] for c in self.candles)
            low = min(c['low'] for c in self.candles)
            close = self.candles[-1]['close']
            open_price = self.candles[0]['open']
            
            return {
                'open': Decimal(str(open_price)),
                'high': Decimal(str(high)),
                'low': Decimal(str(low)),
                'close': Decimal(str(close)),
                'timestamp': self.candles[-1]['timestamp'],
                'candle_count': len(self.candles)
            }
        
        except Exception as e:
            logger.error(f"Error aggregating OHLCV: {e}")
            return {}
    
    def get_price_extremes(self) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Find highest and lowest candles during evaluation period
        
        Returns:
            Tuple of (high_candle_dict, low_candle_dict)
        """
        if not self.candles:
            return None, None
        
        high_candle = max(self.candles, key=lambda c: c['high'])
        low_candle = min(self.candles, key=lambda c: c['low'])
        
        return high_candle, low_candle
    
    def simulate_price_path(self) -> List[Tuple[float, float]]:
        """
        Generate price path for visualization
        
        Returns:
            List of (timestamp_float, price) tuples
        """
        path = []
        for candle in self.candles:
            ts = candle['timestamp'].timestamp() if hasattr(candle['timestamp'], 'timestamp') else 0
            # Add OHLC points for each candle
            path.append((ts, candle['open']))
            path.append((ts + 0.25, candle['high']))
            path.append((ts + 0.5, candle['low']))
            path.append((ts + 0.75, candle['close']))
        
        return path


class PatternReDetector:
    """
    Re-validates technical patterns that were detected in original insight
    
    Checks if BOS, FVG, OB, breakouts actually occurred in replay data
    """
    
    def __init__(self, insight, candles: List[Dict]):
        """
        Initialize pattern re-detector
        
        Args:
            insight: Signal instance
            candles: List of OHLCV candle dicts
        """
        self.insight = insight
        self.candles = candles
        self.detection_results = {}
    
    def verify_all_patterns(self) -> Dict:
        """
        Run all pattern verification checks
        
        Returns:
            Dictionary with verification results
        """
        results = {
            'verified': False,
            'confidence': 0.0,
            'patterns': {},
            'mismatches': []
        }
        
        try:
            # Get original pattern data from insight
            original_patterns = self._extract_original_patterns()
            
            if not original_patterns:
                logger.warning(f"No patterns found in insight #{self.insight.id}")
                return results
            
            # Verify each pattern type
            checks = []
            
            if 'bos' in original_patterns:
                bos_valid = self.verify_bos(original_patterns['bos'])
                results['patterns']['bos'] = bos_valid
                checks.append(bos_valid)
            
            if 'fvg' in original_patterns:
                fvg_valid = self.verify_fvg(original_patterns['fvg'])
                results['patterns']['fvg'] = fvg_valid
                checks.append(fvg_valid)
            
            if 'order_block' in original_patterns:
                ob_valid = self.verify_order_block(original_patterns['order_block'])
                results['patterns']['order_block'] = ob_valid
                checks.append(ob_valid)
            
            if 'breakout' in original_patterns:
                breakout_valid = self.verify_breakout(original_patterns['breakout'])
                results['patterns']['breakout'] = breakout_valid
                checks.append(breakout_valid)
            
            # Calculate overall verification
            if checks:
                verified_count = sum(1 for c in checks if c)
                results['verified'] = all(checks)
                results['confidence'] = (verified_count / len(checks)) * 100
            
            logger.info(
                f"Pattern verification for insight #{self.insight.id}: "
                f"{results['confidence']:.0f}% match"
            )
            
            return results
        
        except Exception as e:
            logger.error(f"Pattern verification error: {e}")
            results['error'] = str(e)
            return results
    
    def _extract_original_patterns(self) -> Dict:
        """Extract pattern data from insight quality_metrics or context_summary"""
        patterns = {}
        
        try:
            # Check if quality_metrics has pattern data
            if hasattr(self.insight, 'quality_metrics') and self.insight.quality_metrics:
                qm = self.insight.quality_metrics
                
                # Look for pattern indicators
                if 'bos_detected' in qm or 'break_of_structure' in qm:
                    patterns['bos'] = True
                
                if 'fvg_detected' in qm or 'fair_value_gap' in qm:
                    patterns['fvg'] = True
                
                if 'order_block' in qm:
                    patterns['order_block'] = True
            
            # Check context_summary for pattern mentions
            if hasattr(self.insight, 'context_summary') and self.insight.context_summary:
                summary = self.insight.context_summary.lower()
                
                if 'bos' in summary or 'break of structure' in summary:
                    patterns['bos'] = True
                
                if 'fvg' in summary or 'fair value gap' in summary:
                    patterns['fvg'] = True
                
                if 'order block' in summary or 'orderblock' in summary:
                    patterns['order_block'] = True
                
                if 'breakout' in summary:
                    patterns['breakout'] = True
            
            return patterns
        
        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return {}
    
    def verify_bos(self, original_data) -> bool:
        """Verify Break of Structure pattern"""
        try:
            if len(self.candles) < 3:
                return False
            
            side = self.insight.side.lower()
            
            # Simple BOS check: look for swing break in direction
            if side in ['buy', 'long']:
                # Check for higher high formation
                highs = [c['high'] for c in self.candles]
                return any(highs[i] > highs[i-1] for i in range(1, len(highs)))
            else:
                # Check for lower low formation
                lows = [c['low'] for c in self.candles]
                return any(lows[i] < lows[i-1] for i in range(1, len(lows)))
        
        except Exception as e:
            logger.error(f"BOS verification error: {e}")
            return False
    
    def verify_fvg(self, original_data) -> bool:
        """Verify Fair Value Gap pattern"""
        try:
            if len(self.candles) < 3:
                return False
            
            # Look for 3-candle gap pattern
            for i in range(len(self.candles) - 2):
                c1, c2, c3 = self.candles[i:i+3]
                
                # Bullish FVG: candle2 high < candle3 low
                if c2['high'] < c3['low']:
                    return True
                
                # Bearish FVG: candle2 low > candle3 high
                if c2['low'] > c3['high']:
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"FVG verification error: {e}")
            return False
    
    def verify_order_block(self, original_data) -> bool:
        """Verify Order Block pattern"""
        try:
            if len(self.candles) < 2:
                return False
            
            side = self.insight.side.lower()
            
            # Simple OB: look for strong directional candle before reversal
            for i in range(len(self.candles) - 1):
                curr = self.candles[i]
                next_candle = self.candles[i+1]
                
                # Calculate candle body size
                curr_body = abs(curr['close'] - curr['open'])
                curr_range = curr['high'] - curr['low']
                
                if curr_range == 0:
                    continue
                
                body_ratio = curr_body / curr_range
                
                # Strong body (>60%) followed by reversal
                if body_ratio > 0.6:
                    if side in ['buy', 'long'] and curr['close'] < curr['open']:
                        # Bearish OB for bullish entry
                        if next_candle['close'] > next_candle['open']:
                            return True
                    elif side in ['sell', 'short'] and curr['close'] > curr['open']:
                        # Bullish OB for bearish entry
                        if next_candle['close'] < next_candle['open']:
                            return True
            
            return False
        
        except Exception as e:
            logger.error(f"Order Block verification error: {e}")
            return False
    
    def verify_breakout(self, original_data) -> bool:
        """Verify Breakout pattern"""
        try:
            if len(self.candles) < 5:
                return False
            
            # Calculate recent high/low levels
            recent_highs = [c['high'] for c in self.candles[:5]]
            recent_lows = [c['low'] for c in self.candles[:5]]
            
            resistance = max(recent_highs)
            support = min(recent_lows)
            
            # Check if price broke through
            for candle in self.candles[5:]:
                if candle['high'] > resistance * 1.001:  # 0.1% buffer
                    return True
                if candle['low'] < support * 0.999:
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Breakout verification error: {e}")
            return False


def replay_insight(insight, horizon_delta: timedelta, broker_api=None) -> Optional[Dict]:
    """
    Convenience function to replay an insight and get aggregated data
    
    Args:
        insight: Signal instance
        horizon_delta: Time period for replay
        broker_api: Optional broker API client (unused with database)
    
    Returns:
        Aggregated OHLCV dict or None
    """
    try:
        replay = OHLCVReplay(insight, horizon_delta)
        
        # Fetch candles using the date range from replay object
        candles = replay.fetch_candles(replay.start_time, replay.end_time)
        
        if not candles:
            return None
        
        # Store candles in replay object
        replay.candles = candles
        
        # Get aggregated OHLCV
        ohlcv = replay.get_aggregated_ohlcv()
        
        # Add pattern verification
        detector = PatternReDetector(insight, candles)
        verification = detector.verify_all_patterns()
        
        ohlcv['pattern_verification'] = verification
        ohlcv['metadata'] = replay.metadata
        
        return ohlcv
    
    except Exception as e:
        logger.error(f"Replay failed for insight #{insight.id}: {e}")
        return None
