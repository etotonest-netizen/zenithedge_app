"""
Zenith Market Analyst - AI Insight Engine

Central intelligence system that converts raw market metadata
into professional, varied, intelligent natural language insights.

Pipeline:
  Raw Metadata → Parser → Scorer → Variation Engine → AI Insights

NO external APIs. NO cloud costs. 100% local intelligence.
"""
import logging
from typing import Dict, Any, Tuple, Optional
from django.utils import timezone
from datetime import datetime

from autopsy.insight_parser import InsightParser
from autopsy.insight_scorer import InsightScorer
from autopsy.variation_engine import VariationEngine

logger = logging.getLogger('autopsy')


class ZenithMarketAnalyst:
    """
    Main AI engine for Visual Insights Mode
    
    Transforms every bar into intelligent market commentary
    """
    
    def __init__(self):
        self.parser = InsightParser()
        self.scorer = InsightScorer()
        self.variation_engine = VariationEngine()
        
        # Load vocabulary from database if available
        try:
            self.variation_engine.load_vocabulary_from_db()
        except Exception as e:
            logger.warning(f"Could not load vocabulary from DB: {e}")
    
    def process_bar(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete processing pipeline for a single bar
        
        Args:
            raw_metadata: JSON from Pine Script webhook
            
        Returns:
            Complete insight object ready for database storage
        """
        try:
            # Step 1: Parse and validate metadata
            parsed = self.parser.parse(raw_metadata)
            
            # Step 2: Calculate insight index and component scores
            insight_index, score_breakdown = self.scorer.calculate_insight_index(parsed)
            
            # Get quality label
            quality_label = self.scorer.get_quality_label(insight_index)
            
            # Step 3: Generate natural language insight
            insight_text, vocab_hash = self.variation_engine.generate_insight(parsed)
            
            # Step 4: Generate actionable suggestion
            suggestion = self.variation_engine.generate_suggestion(parsed)
            
            # Step 5: Extract chart labels
            chart_labels = self.parser.extract_chart_labels(parsed)
            
            # Step 6: Integrate news context (if available)
            news_context = self._get_news_context(parsed)
            
            # Build complete insight object
            insight_data = {
                # Core identification
                'symbol': parsed['symbol'],
                'timeframe': parsed['timeframe'],
                'timestamp': parsed['timestamp'],
                
                # Market metadata
                'regime': parsed['regime'],
                'structure': parsed['structure'],
                'momentum': parsed['momentum'],
                'volume_state': parsed['volume_state'],
                'session': parsed['session'],
                'expected_behavior': parsed['expected_behavior'],
                'strength': parsed['strength'],
                'risk_notes': parsed['risk_notes'],
                
                # AI-generated content
                'insight_text': insight_text,
                'suggestion': suggestion,
                'insight_index': insight_index,
                'quality_label': quality_label,
                
                # Scoring breakdown
                'structure_clarity': score_breakdown['structure_clarity'],
                'regime_stability': score_breakdown['regime_stability'],
                'volume_quality': score_breakdown['volume_quality'],
                'momentum_alignment': score_breakdown['momentum_alignment'],
                'session_validity': score_breakdown['session_validity'],
                'risk_level': score_breakdown['risk_level'],
                
                # News integration
                'news_impact': news_context.get('impact', ''),
                'news_context': news_context.get('context', ''),
                
                # Chart labels
                'chart_labels': chart_labels,
                
                # Variation tracking
                'vocabulary_hash': vocab_hash,
                
                # Raw data
                'raw_metadata': parsed['raw_metadata'],
            }
            
            logger.info(f"Processed insight for {parsed['symbol']} {parsed['timeframe']}: "
                       f"Index={insight_index}, Hash={vocab_hash[:8]}")
            
            return insight_data
            
        except Exception as e:
            logger.error(f"Error processing bar: {e}", exc_info=True)
            raise
    
    def _get_news_context(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Get relevant news context for this market moment
        
        Integrates with zennews app
        """
        try:
            from zennews.models import NewsEvent
            from django.db.models import Q
            from datetime import timedelta
            
            symbol = metadata['symbol']
            timestamp = metadata['timestamp']
            
            # Get news within +/- 4 hours
            time_window_start = timestamp - timedelta(hours=4)
            time_window_end = timestamp + timedelta(hours=4)
            
            # Find relevant news
            relevant_news = NewsEvent.objects.filter(
                Q(impact_level__in=['high', 'medium']) &
                Q(published_at__gte=time_window_start) &
                Q(published_at__lte=time_window_end)
            ).filter(
                Q(headline__icontains=symbol[:3]) |  # Currency pair
                Q(symbol__icontains=symbol[:3])
            ).order_by('-impact_level', 'published_at')[:3]
            
            if not relevant_news:
                return {'impact': 'none', 'context': ''}
            
            # Build context string
            news_items = []
            highest_impact = 'none'
            
            for news in relevant_news:
                time_diff = (news.published_at - timestamp).total_seconds() / 60
                
                if abs(time_diff) < 60:  # Within 1 hour
                    if time_diff > 0:
                        time_str = f"in {int(time_diff)} minutes"
                    else:
                        time_str = f"{int(abs(time_diff))} minutes ago"
                else:
                    hours = abs(time_diff) / 60
                    time_str = f"{int(hours)} hours ago" if time_diff < 0 else f"in {int(hours)} hours"
                
                news_items.append(f"{news.headline} {time_str}")
                
                if news.impact_level == 'high':
                    highest_impact = 'high'
                elif news.impact_level == 'medium' and highest_impact != 'high':
                    highest_impact = 'medium'
                elif highest_impact == 'none':
                    highest_impact = 'low'
            
            context_text = ". ".join(news_items) if news_items else ""
            
            return {
                'impact': highest_impact,
                'context': context_text
            }
            
        except Exception as e:
            logger.warning(f"Could not fetch news context: {e}")
            return {'impact': '', 'context': ''}
    
    def save_insight(self, insight_data: Dict[str, Any]) -> Any:
        """
        Save insight to database
        
        Args:
            insight_data: Complete insight dictionary
            
        Returns:
            MarketInsight instance
        """
        from autopsy.models import MarketInsight
        
        try:
            # Remove quality_label as it's not a model field (used only for API responses)
            db_data = {k: v for k, v in insight_data.items() if k != 'quality_label'}
            
            insight = MarketInsight.objects.create(**db_data)
            
            logger.info(f"Saved insight #{insight.id}: {insight.symbol} {insight.timeframe}")
            
            return insight
            
        except Exception as e:
            logger.error(f"Error saving insight: {e}", exc_info=True)
            raise
    
    def get_latest_insights(self, symbol: str = None, timeframe: str = None, 
                           limit: int = 50) -> list:
        """
        Retrieve latest insights for UI display
        
        Args:
            symbol: Filter by symbol (optional)
            timeframe: Filter by timeframe (optional)
            limit: Maximum number of insights to return
            
        Returns:
            List of MarketInsight objects
        """
        try:
            from autopsy.models import MarketInsight
            
            queryset = MarketInsight.objects.all()
            
            if symbol:
                queryset = queryset.filter(symbol=symbol)
            
            if timeframe:
                queryset = queryset.filter(timeframe=timeframe)
            
            insights = queryset.order_by('-timestamp')[:limit]
            
            return list(insights)
            
        except Exception as e:
            logger.error(f"Error retrieving insights: {e}")
            return []
    
    def get_insight_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get statistical summary of recent insights
        
        Used for dashboard analytics
        """
        try:
            from autopsy.models import MarketInsight
            from django.db.models import Avg, Count, Max, Min
            from datetime import timedelta
            
            cutoff = timezone.now() - timedelta(hours=hours)
            
            insights = MarketInsight.objects.filter(created_at__gte=cutoff)
            
            stats = insights.aggregate(
                total_count=Count('id'),
                avg_index=Avg('insight_index'),
                max_index=Max('insight_index'),
                min_index=Min('insight_index'),
                avg_structure_clarity=Avg('structure_clarity'),
                avg_regime_stability=Avg('regime_stability'),
            )
            
            # Regime distribution
            regime_dist = insights.values('regime').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Structure distribution
            structure_dist = insights.values('structure').annotate(
                count=Count('id')
            ).order_by('-count')
            
            # Session distribution
            session_dist = insights.values('session').annotate(
                count=Count('id')
            ).order_by('-count')
            
            return {
                'summary': stats,
                'regime_distribution': list(regime_dist),
                'structure_distribution': list(structure_dist),
                'session_distribution': list(session_dist),
                'timeframe': f"Last {hours} hours",
            }
            
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def test_insight_generation(self, sample_count: int = 10) -> list:
        """
        Generate test insights for QA validation
        
        Returns list of (metadata, insight) tuples
        """
        import random
        
        test_results = []
        
        # Sample metadata templates
        regimes = ['trending', 'ranging', 'volatile', 'consolidation']
        structures = ['bos', 'choch', 'pullback', 'liquidity_sweep', 'fvg', 'order_block', 'compression']
        momentums = ['increasing', 'decreasing', 'diverging', 'neutral']
        volumes = ['spike', 'drop', 'normal']
        sessions = ['london', 'newyork', 'asia', 'off']
        
        for i in range(sample_count):
            # Generate random metadata
            metadata = {
                'symbol': random.choice(['EURUSD', 'GBPUSD', 'USDJPY', 'XAUUSD']),
                'timeframe': random.choice(['5m', '15m', '1H', '4H']),
                'timestamp': timezone.now().isoformat(),
                'regime': random.choice(regimes),
                'structure': random.choice(structures),
                'momentum': random.choice(momentums),
                'volume_state': random.choice(volumes),
                'session': random.choice(sessions),
                'expected_behavior': random.choice(['Expansion', 'Retracement', 'Reversal', 'Liquidity grab']),
                'strength': random.randint(30, 95),
                'risk_notes': random.sample(['High volatility', 'News risk', 'Low liquidity'], k=random.randint(0, 2)),
            }
            
            try:
                insight_data = self.process_bar(metadata)
                test_results.append((metadata, insight_data))
                
                print(f"\n{'='*80}")
                print(f"Test #{i+1}: {metadata['symbol']} {metadata['timeframe']}")
                print(f"Regime: {metadata['regime']}, Structure: {metadata['structure']}")
                print(f"Insight Index: {insight_data['insight_index']}/100")
                print(f"Insight: {insight_data['insight_text']}")
                print(f"Suggestion: {insight_data['suggestion']}")
                print(f"Hash: {insight_data['vocabulary_hash']}")
                
            except Exception as e:
                logger.error(f"Test {i+1} failed: {e}")
        
        return test_results


# Singleton instance
analyst = ZenithMarketAnalyst()
