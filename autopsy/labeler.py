"""
Outcome Labeling Engine

Configurable rule-based system to determine insight outcomes based on
real-world price action and performance metrics.
"""
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple
from django.utils import timezone
from datetime import timedelta

from .models import OutcomeChoices, LabelingRule, InsightAudit

logger = logging.getLogger(__name__)


class OutcomeLabeler:
    """
    Evaluates insight outcomes using configurable rules
    
    Supports multiple horizons and custom success/failure criteria
    """
    
    # Default pip values for each symbol
    PIP_VALUES = {
        'EURUSD': 0.0001,
        'GBPUSD': 0.0001,
        'USDJPY': 0.01,
        'USDCHF': 0.0001,
        'AUDUSD': 0.0001,
        'NZDUSD': 0.0001,
        'USDCAD': 0.0001,
        'XAUUSD': 0.10,  # Gold
        'XAGUSD': 0.01,  # Silver
    }
    
    def __init__(self, insight, horizon='4H', config=None):
        """
        Initialize labeler for an insight
        
        Args:
            insight: Signal model instance
            horizon: Evaluation timeframe (1H, 4H, 24H, 7D)
            config: Override configuration dict
        """
        self.insight = insight
        self.horizon = horizon
        self.config = config or {}
        
        # Get applicable labeling rule
        self.rule = self._get_matching_rule()
        
        # Calculate horizon timedelta
        self.horizon_delta = self._parse_horizon(horizon)
        
        # Get pip value for symbol
        self.pip_value = self._get_pip_value()
    
    def _get_matching_rule(self) -> Optional[LabelingRule]:
        """Find most specific matching labeling rule"""
        rules = LabelingRule.objects.filter(
            is_active=True,
            horizon=self.horizon
        ).order_by('-priority')
        
        for rule in rules:
            if rule.matches(self.insight):
                logger.info(f"Using labeling rule #{rule.id} for {self.insight.symbol}")
                return rule
        
        logger.warning(f"No matching rule for {self.insight.symbol} {self.horizon}")
        return None
    
    def _parse_horizon(self, horizon: str) -> timedelta:
        """Convert horizon string to timedelta"""
        mapping = {
            '1H': timedelta(hours=1),
            '4H': timedelta(hours=4),
            '24H': timedelta(hours=24),
            '7D': timedelta(days=7),
            '1D': timedelta(days=1),
            '1W': timedelta(weeks=1),
        }
        return mapping.get(horizon, timedelta(hours=4))
    
    def _get_pip_value(self) -> Decimal:
        """Get pip value for insight symbol"""
        symbol = self.insight.symbol.upper()
        
        # Direct match
        if symbol in self.PIP_VALUES:
            return Decimal(str(self.PIP_VALUES[symbol]))
        
        # Check if JPY pair
        if 'JPY' in symbol:
            return Decimal('0.01')
        
        # Check if metals
        if 'XAU' in symbol or 'GOLD' in symbol:
            return Decimal('0.10')
        if 'XAG' in symbol or 'SILVER' in symbol:
            return Decimal('0.01')
        
        # Default for forex
        return Decimal('0.0001')
    
    def calculate_pips(self, price_diff: Decimal) -> Decimal:
        """Convert price difference to pips"""
        return abs(price_diff) / self.pip_value
    
    def evaluate(self, ohlcv_data: Dict) -> Tuple[str, Dict]:
        """
        Evaluate insight outcome using OHLCV data
        
        Args:
            ohlcv_data: Dictionary with OHLC prices and timestamps
                {
                    'high': Decimal,
                    'low': Decimal,
                    'close': Decimal,
                    'open': Decimal,
                    'timestamp': datetime
                }
        
        Returns:
            Tuple of (outcome, metrics_dict)
        """
        try:
            entry_price = Decimal(str(self.insight.price))
            side = self.insight.side.lower()
            
            high = Decimal(str(ohlcv_data['high']))
            low = Decimal(str(ohlcv_data['low']))
            close = Decimal(str(ohlcv_data['close']))
            
            # Calculate price movement
            if side == 'buy' or side == 'long':
                favorable_move = high - entry_price
                adverse_move = entry_price - low
                exit_price = close
                pnl_pct = ((close - entry_price) / entry_price) * 100
            else:  # sell/short
                favorable_move = entry_price - low
                adverse_move = high - entry_price
                exit_price = close
                pnl_pct = ((entry_price - close) / entry_price) * 100
            
            # Convert to pips
            favorable_pips = self.calculate_pips(favorable_move)
            adverse_pips = self.calculate_pips(adverse_move)
            
            # Build metrics
            metrics = {
                'entry_price': float(entry_price),
                'exit_price': float(exit_price),
                'high_price': float(high),
                'low_price': float(low),
                'pnl_pct': float(pnl_pct),
                'max_drawdown': float(adverse_pips),
                'max_favorable': float(favorable_pips),
                'favorable_move_pips': float(favorable_pips),
                'adverse_move_pips': float(adverse_pips),
            }
            
            # Determine outcome using rules
            outcome = self._determine_outcome(
                favorable_pips=favorable_pips,
                adverse_pips=adverse_pips,
                pnl_pct=Decimal(str(pnl_pct))
            )
            
            # Calculate risk/reward if we have rule
            if self.rule and self.rule.success_tp_pips and self.rule.fail_sl_pips:
                rr = float(self.rule.success_tp_pips / self.rule.fail_sl_pips) if self.rule.fail_sl_pips else 0
                metrics['risk_reward_actual'] = rr
            
            logger.info(
                f"Labeled {self.insight.symbol} #{self.insight.id}: {outcome} "
                f"(+{favorable_pips:.1f} pips / -{adverse_pips:.1f} pips)"
            )
            
            return outcome, metrics
            
        except Exception as e:
            logger.error(f"Error evaluating insight #{self.insight.id}: {e}")
            return OutcomeChoices.NEEDS_REVIEW, {'error': str(e)}
    
    def _determine_outcome(
        self, 
        favorable_pips: Decimal, 
        adverse_pips: Decimal,
        pnl_pct: Decimal
    ) -> str:
        """
        Apply rules to determine outcome
        
        Priority:
        1. Check if failed (hit stop loss)
        2. Check if succeeded (hit take profit)
        3. Check if neutral (small movement)
        4. Default to needs_review
        """
        # Use rule if available, otherwise defaults
        if self.rule:
            success_tp = self.rule.success_tp_pips or Decimal('20')
            fail_sl = self.rule.fail_sl_pips or Decimal('15')
            neutral_band = self.rule.neutral_band_pips or Decimal('10')
        else:
            # Default conservative rules
            success_tp = Decimal('20')
            fail_sl = Decimal('15')
            neutral_band = Decimal('10')
        
        # Check failure first
        if adverse_pips >= fail_sl:
            return OutcomeChoices.FAILED
        
        # Check success
        if favorable_pips >= success_tp:
            return OutcomeChoices.SUCCEEDED
        
        # Check neutral zone
        if favorable_pips <= neutral_band and adverse_pips <= neutral_band:
            return OutcomeChoices.NEUTRAL
        
        # Moderate movement but didn't hit targets
        if favorable_pips > adverse_pips and pnl_pct > Decimal('0.5'):
            return OutcomeChoices.SUCCEEDED
        
        if adverse_pips > favorable_pips and pnl_pct < Decimal('-0.5'):
            return OutcomeChoices.FAILED
        
        # Ambiguous case
        return OutcomeChoices.NEUTRAL
    
    def create_audit(self, ohlcv_data: Dict, **kwargs) -> InsightAudit:
        """
        Evaluate and create InsightAudit record
        
        Args:
            ohlcv_data: OHLCV price data dict
            **kwargs: Additional fields for InsightAudit
        
        Returns:
            InsightAudit instance
        """
        outcome, metrics = self.evaluate(ohlcv_data)
        
        # Convert OHLCV data to JSON-serializable format
        def serialize_value(val):
            """Convert Decimal/datetime to JSON-serializable types"""
            if isinstance(val, Decimal):
                return float(val)
            elif hasattr(val, 'isoformat'):  # datetime
                return val.isoformat()
            return val
        
        # Serialize replay snapshot
        serialized_ohlcv = {
            k: serialize_value(v) for k, v in ohlcv_data.items()
        }
        
        # Build audit record
        audit_data = {
            'insight': self.insight,
            'user': self.insight.user,
            'horizon': self.horizon,
            'outcome': outcome,
            'pnl_pct': metrics.get('pnl_pct'),
            'max_drawdown': metrics.get('max_drawdown'),
            'entry_price': metrics.get('entry_price'),
            'exit_price': metrics.get('exit_price'),
            'high_price': metrics.get('high_price'),
            'low_price': metrics.get('low_price'),
            'risk_reward_actual': metrics.get('risk_reward_actual'),
            'replay_snapshot': serialized_ohlcv,
            'config_snapshot': {
                'rule_id': self.rule.id if self.rule else None,
                'horizon': self.horizon,
                'pip_value': float(self.pip_value),
            }
        }
        
        # Merge any additional kwargs
        audit_data.update(kwargs)
        
        # Create audit
        audit = InsightAudit.objects.create(**audit_data)
        
        logger.info(f"Created audit #{audit.id} for insight #{self.insight.id}: {outcome}")
        
        return audit


class BatchLabeler:
    """
    Batch labeling for multiple insights
    """
    
    def __init__(self, insights, horizons=None):
        """
        Initialize batch labeler
        
        Args:
            insights: QuerySet or list of Signal instances
            horizons: List of horizon strings (default: ['4H', '24H'])
        """
        self.insights = insights
        self.horizons = horizons or ['4H', '24H']
        self.stats = {
            'total': 0,
            'succeeded': 0,
            'failed': 0,
            'neutral': 0,
            'pending': 0,
            'needs_review': 0,
            'errors': 0
        }
    
    def process_all(self, fetch_ohlcv_func, progress_callback=None):
        """
        Process all insights with given OHLCV fetcher
        
        Args:
            fetch_ohlcv_func: Function(insight, horizon) -> ohlcv_data dict
            progress_callback: Optional callback(current, total, insight)
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.insights) if hasattr(self.insights, '__len__') else self.insights.count()
        self.stats['total'] = total
        
        for idx, insight in enumerate(self.insights):
            if progress_callback:
                progress_callback(idx + 1, total, insight)
            
            for horizon in self.horizons:
                try:
                    # Check if audit already exists
                    if InsightAudit.objects.filter(insight=insight, horizon=horizon).exists():
                        logger.debug(f"Audit already exists for insight #{insight.id} {horizon}")
                        continue
                    
                    # Fetch OHLCV data
                    ohlcv_data = fetch_ohlcv_func(insight, horizon)
                    
                    if not ohlcv_data:
                        logger.warning(f"No OHLCV data for insight #{insight.id}")
                        continue
                    
                    # Create labeler and audit
                    labeler = OutcomeLabeler(insight, horizon)
                    audit = labeler.create_audit(ohlcv_data)
                    
                    # Update stats
                    outcome_key = audit.outcome
                    if outcome_key in self.stats:
                        self.stats[outcome_key] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing insight #{insight.id}: {e}")
                    self.stats['errors'] += 1
        
        return self.stats
    
    def get_summary(self) -> str:
        """Get human-readable summary"""
        if self.stats['total'] == 0:
            return "No insights processed"
        
        return (
            f"Processed {self.stats['total']} insights:\n"
            f"  ✅ Succeeded: {self.stats['succeeded']}\n"
            f"  ❌ Failed: {self.stats['failed']}\n"
            f"  ⚪ Neutral: {self.stats['neutral']}\n"
            f"  ⏳ Pending: {self.stats['pending']}\n"
            f"  ⚠️  Needs Review: {self.stats['needs_review']}\n"
            f"  💥 Errors: {self.stats['errors']}"
        )


def label_insight(insight, horizon='4H', ohlcv_data=None) -> Optional[InsightAudit]:
    """
    Convenience function to label a single insight
    
    Args:
        insight: Signal instance
        horizon: Evaluation timeframe
        ohlcv_data: Optional pre-fetched OHLCV data
    
    Returns:
        InsightAudit instance or None if error
    """
    try:
        labeler = OutcomeLabeler(insight, horizon)
        
        if ohlcv_data is None:
            # Would need to fetch OHLCV here
            logger.error("OHLCV data required")
            return None
        
        return labeler.create_audit(ohlcv_data)
    
    except Exception as e:
        logger.error(f"Failed to label insight #{insight.id}: {e}")
        return None
