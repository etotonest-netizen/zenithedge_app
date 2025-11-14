"""
Root Cause Analysis (RCA) Engine

Analyzes failed/neutral insights to determine probable causes using
multiple heuristics and evidence sources.
"""
import logging
from typing import List, Dict, Tuple
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg, Q

from .models import RCACauseChoices, AuditRCA, OutcomeChoices

logger = logging.getLogger(__name__)


class RCAEngine:
    """
    Multi-heuristic root cause analyzer
    
    Examines news events, regime shifts, volatility, model attribution,
    and detector accuracy to identify failure causes.
    """
    
    def __init__(self, audit):
        """
        Initialize RCA for an audit
        
        Args:
            audit: InsightAudit instance
        """
        self.audit = audit
        self.insight = audit.insight
        self.causes = []
        self.evidence = {}
    
    def analyze(self) -> List[AuditRCA]:
        """
        Run full RCA pipeline and create cause records
        
        Returns:
            List of AuditRCA instances, ranked by confidence
        """
        try:
            # Run all heuristic checks
            self._check_news_impact()
            self._check_regime_drift()
            self._check_volatility_spike()
            self._check_model_error()
            self._check_detector_accuracy()
            self._check_spread_slippage()
            self._check_false_positive()
            
            # Rank causes by confidence
            self.causes.sort(key=lambda x: x['confidence'], reverse=True)
            
            # Create RCA records
            rca_records = []
            for rank, cause_data in enumerate(self.causes[:5], 1):  # Top 5 causes
                rca = AuditRCA.objects.create(
                    audit=self.audit,
                    cause=cause_data['cause'],
                    confidence=cause_data['confidence'],
                    rank=rank,
                    summary=cause_data['summary'],
                    evidence=cause_data['evidence'],
                    explain_shap=cause_data.get('explain_shap', {}),
                    news_references=cause_data.get('news_references', [])
                )
                rca_records.append(rca)
            
            logger.info(
                f"RCA for audit #{self.audit.id}: identified {len(rca_records)} causes, "
                f"primary: {rca_records[0].get_cause_display() if rca_records else 'None'}"
            )
            
            return rca_records
        
        except Exception as e:
            logger.error(f"RCA analysis failed for audit #{self.audit.id}: {e}")
            return []
    
    def _check_news_impact(self):
        """Check if news event caused failure"""
        try:
            from zennews.models import NewsEvent
            
            # Look for news ±30 minutes around insight
            window_start = self.insight.received_at - timedelta(minutes=30)
            window_end = self.insight.received_at + timedelta(minutes=30)
            
            news_events = NewsEvent.objects.filter(
                symbol__iexact=self.insight.symbol,
                timestamp__gte=window_start,
                timestamp__lte=window_end
            ).order_by('-timestamp')
            
            if not news_events.exists():
                return
            
            # Calculate impact score
            high_impact_count = sum(1 for n in news_events if self._get_news_impact(n) > 0.6)
            
            if high_impact_count > 0:
                confidence = min(85, 50 + (high_impact_count * 15))
                
                headlines = [n.headline for n in news_events[:3]]
                news_ids = [n.id for n in news_events]
                
                self.causes.append({
                    'cause': RCACauseChoices.NEWS_SHOCK,
                    'confidence': Decimal(str(confidence)),
                    'summary': f"High-impact news detected: {high_impact_count} event(s) within ±30min. "
                               f"Headlines: {'; '.join(headlines[:2])}",
                    'evidence': {
                        'news_count': high_impact_count,
                        'headlines': headlines,
                        'timing_minutes': [
                            (n.timestamp - self.insight.received_at).total_seconds() / 60
                            for n in news_events
                        ]
                    },
                    'news_references': news_ids
                })
                
                logger.debug(f"News impact detected: {high_impact_count} events")
        
        except ImportError:
            logger.warning("ZenNews not available for RCA")
        except Exception as e:
            logger.error(f"News impact check error: {e}")
    
    def _get_news_impact(self, news_event) -> float:
        """Estimate news impact (0-1 scale)"""
        # Simple heuristic based on keywords
        headline = news_event.headline.lower()
        
        high_impact_keywords = [
            'fed', 'ecb', 'boe', 'rate', 'decision', 'inflation',
            'gdp', 'employment', 'crisis', 'emergency', 'breaks'
        ]
        
        medium_impact_keywords = [
            'data', 'report', 'forecast', 'outlook', 'warning',
            'growth', 'trade', 'policy'
        ]
        
        # Count keyword matches
        high_matches = sum(1 for kw in high_impact_keywords if kw in headline)
        medium_matches = sum(1 for kw in medium_impact_keywords if kw in headline)
        
        if high_matches > 0:
            return 0.8
        if medium_matches > 1:
            return 0.6
        if medium_matches > 0:
            return 0.4
        
        return 0.2
    
    def _check_regime_drift(self):
        """Check if market regime changed"""
        try:
            from cognition.models import RegimeClassification
            
            # Get regime at insight time and 1 hour later
            insight_time = self.insight.received_at
            later_time = insight_time + timedelta(hours=1)
            
            regime_at_insight = RegimeClassification.objects.filter(
                symbol=self.insight.symbol,
                timestamp__lte=insight_time
            ).order_by('-timestamp').first()
            
            regime_later = RegimeClassification.objects.filter(
                symbol=self.insight.symbol,
                timestamp__gte=insight_time,
                timestamp__lte=later_time
            ).order_by('timestamp').first()
            
            if not regime_at_insight or not regime_later:
                return
            
            # Check if regime changed
            if regime_at_insight.regime != regime_later.regime:
                confidence_drop = abs(
                    regime_at_insight.confidence - regime_later.confidence
                )
                
                confidence = min(75, 40 + confidence_drop)
                
                self.causes.append({
                    'cause': RCACauseChoices.REGIME_DRIFT,
                    'confidence': Decimal(str(confidence)),
                    'summary': f"Regime shifted from {regime_at_insight.regime} to "
                               f"{regime_later.regime} during evaluation period.",
                    'evidence': {
                        'regime_before': regime_at_insight.regime,
                        'regime_after': regime_later.regime,
                        'confidence_before': float(regime_at_insight.confidence),
                        'confidence_after': float(regime_later.confidence),
                        'confidence_drop': float(confidence_drop)
                    }
                })
                
                logger.debug(
                    f"Regime drift detected: {regime_at_insight.regime} → {regime_later.regime}"
                )
        
        except ImportError:
            logger.debug("Cognition module not available")
        except Exception as e:
            logger.error(f"Regime drift check error: {e}")
    
    def _check_volatility_spike(self):
        """Check for abnormal volatility"""
        try:
            # Calculate price range during evaluation
            if not self.audit.high_price or not self.audit.low_price:
                return
            
            price_range = float(self.audit.high_price - self.audit.low_price)
            entry_price = float(self.audit.entry_price)
            
            if entry_price == 0:
                return
            
            volatility_pct = (price_range / entry_price) * 100
            
            # Compare to historical average
            from .models import InsightAudit
            
            avg_volatility = InsightAudit.objects.filter(
                insight__symbol=self.insight.symbol,
                insight__timeframe=self.insight.timeframe,
                high_price__isnull=False,
                low_price__isnull=False
            ).exclude(id=self.audit.id).aggregate(
                avg_range=Avg(
                    (F('high_price') - F('low_price')) / F('entry_price') * 100
                )
            )['avg_range'] or 0.5
            
            # Check if current volatility is significantly higher
            if volatility_pct > avg_volatility * 2:
                confidence = min(70, 35 + (volatility_pct / avg_volatility) * 10)
                
                self.causes.append({
                    'cause': RCACauseChoices.VOLATILITY_SPIKE,
                    'confidence': Decimal(str(confidence)),
                    'summary': f"Volatility spike detected: {volatility_pct:.2f}% range "
                               f"(avg: {avg_volatility:.2f}%)",
                    'evidence': {
                        'volatility_pct': volatility_pct,
                        'avg_volatility': avg_volatility,
                        'spike_ratio': volatility_pct / avg_volatility
                    }
                })
                
                logger.debug(f"Volatility spike: {volatility_pct:.2f}%")
        
        except Exception as e:
            logger.error(f"Volatility check error: {e}")
    
    def _check_model_error(self):
        """Check for model prediction errors using feature importance"""
        try:
            # Check if confidence was low but insight was accepted
            from signals.models import TradeValidation
            
            validation = TradeValidation.objects.filter(
                signal=self.insight
            ).order_by('-created_at').first()
            
            if not validation:
                return
            
            ai_score = validation.ai_score or 50
            confidence = validation.confidence or 0
            
            # Low confidence but outcome failed = model uncertainty
            if confidence < 70 and self.audit.outcome == OutcomeChoices.FAILED:
                conf_score = 60 + (70 - confidence) / 2
                
                self.causes.append({
                    'cause': RCACauseChoices.MODEL_ERROR,
                    'confidence': Decimal(str(conf_score)),
                    'summary': f"Model had low confidence ({confidence:.0f}%) and failed as expected. "
                               f"Feature weights may need rebalancing.",
                    'evidence': {
                        'ai_score': float(ai_score),
                        'confidence': float(confidence),
                        'prediction_quality': 'low_confidence'
                    }
                })
            
            # High confidence but failed = model overconfidence
            elif confidence > 80 and self.audit.outcome == OutcomeChoices.FAILED:
                self.causes.append({
                    'cause': RCACauseChoices.MODEL_ERROR,
                    'confidence': Decimal('75'),
                    'summary': f"Model showed high confidence ({confidence:.0f}%) but trade failed. "
                               f"Possible overconfidence or missing features.",
                    'evidence': {
                        'ai_score': float(ai_score),
                        'confidence': float(confidence),
                        'prediction_quality': 'overconfident'
                    }
                })
        
        except Exception as e:
            logger.error(f"Model error check failed: {e}")
    
    def _check_detector_accuracy(self):
        """Check if pattern was mis-detected"""
        try:
            if not self.audit.replay_verified:
                # Pattern was not verified in replay
                confidence = 65
                
                self.causes.append({
                    'cause': RCACauseChoices.DETECTOR_MISIDENTIFICATION,
                    'confidence': Decimal(str(confidence)),
                    'summary': "Pattern could not be verified during replay. "
                               "Original detection may have been false positive.",
                    'evidence': {
                        'replay_verified': False,
                        'pattern_confidence': 'failed_reverification'
                    }
                })
                
                logger.debug("Detector mis-identification: pattern not verified")
        
        except Exception as e:
            logger.error(f"Detector check error: {e}")
    
    def _check_spread_slippage(self):
        """Check for excessive spread or slippage"""
        try:
            if not self.audit.slippage_pips:
                return
            
            slippage = float(self.audit.slippage_pips)
            
            # Slippage > 3 pips is significant
            if slippage > 3:
                confidence = min(60, 30 + slippage * 5)
                
                self.causes.append({
                    'cause': RCACauseChoices.SPREAD_SLIPPAGE,
                    'confidence': Decimal(str(confidence)),
                    'summary': f"High slippage detected: {slippage:.1f} pips. "
                               f"May indicate liquidity issues.",
                    'evidence': {
                        'slippage_pips': slippage,
                        'threshold': 3.0
                    }
                })
        
        except Exception as e:
            logger.error(f"Slippage check error: {e}")
    
    def _check_false_positive(self):
        """Check if pattern was a false positive"""
        try:
            from .models import InsightAudit
            
            # Check success rate for this strategy+symbol
            recent_audits = InsightAudit.objects.filter(
                insight__symbol=self.insight.symbol,
                insight__timeframe=self.insight.timeframe,
                horizon=self.audit.horizon
            ).exclude(
                outcome=OutcomeChoices.PENDING
            ).order_by('-evaluated_at')[:20]
            
            if recent_audits.count() < 5:
                return
            
            failed_count = sum(
                1 for a in recent_audits 
                if a.outcome == OutcomeChoices.FAILED
            )
            
            fail_rate = (failed_count / recent_audits.count()) * 100
            
            # High failure rate suggests systematic false positives
            if fail_rate > 60:
                confidence = min(70, 40 + (fail_rate - 60))
                
                self.causes.append({
                    'cause': RCACauseChoices.FALSE_POSITIVE,
                    'confidence': Decimal(str(confidence)),
                    'summary': f"Strategy has high failure rate ({fail_rate:.0f}%) "
                               f"for {self.insight.symbol}. Pattern may be unreliable.",
                    'evidence': {
                        'fail_rate': fail_rate,
                        'sample_size': recent_audits.count(),
                        'failed_count': failed_count
                    }
                })
                
                logger.debug(f"False positive pattern: {fail_rate:.0f}% fail rate")
        
        except Exception as e:
            logger.error(f"False positive check error: {e}")


def analyze_audit(audit) -> List[AuditRCA]:
    """
    Convenience function to run RCA on an audit
    
    Args:
        audit: InsightAudit instance
    
    Returns:
        List of AuditRCA records
    """
    try:
        engine = RCAEngine(audit)
        return engine.analyze()
    except Exception as e:
        logger.error(f"RCA failed for audit #{audit.id}: {e}")
        return []


def batch_analyze(audits, progress_callback=None) -> Dict:
    """
    Run RCA on multiple audits
    
    Args:
        audits: QuerySet or list of InsightAudit instances
        progress_callback: Optional callback(current, total, audit)
    
    Returns:
        Statistics dictionary
    """
    stats = {
        'total': 0,
        'analyzed': 0,
        'causes_found': 0,
        'errors': 0,
        'top_causes': {}
    }
    
    total = len(audits) if hasattr(audits, '__len__') else audits.count()
    stats['total'] = total
    
    for idx, audit in enumerate(audits):
        if progress_callback:
            progress_callback(idx + 1, total, audit)
        
        try:
            # Skip if audit already has RCA
            if audit.root_causes.exists():
                logger.debug(f"RCA already exists for audit #{audit.id}")
                continue
            
            # Run RCA
            causes = analyze_audit(audit)
            
            if causes:
                stats['analyzed'] += 1
                stats['causes_found'] += len(causes)
                
                # Track top cause
                top_cause = causes[0].cause
                stats['top_causes'][top_cause] = stats['top_causes'].get(top_cause, 0) + 1
        
        except Exception as e:
            logger.error(f"Batch RCA error for audit #{audit.id}: {e}")
            stats['errors'] += 1
    
    return stats


# Add F import for Django ORM
from django.db.models import F
