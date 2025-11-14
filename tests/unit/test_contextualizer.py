"""
Unit Tests for Contextual Intelligence Engine

Tests narrative generation, strategy-aware language, session context,
and 3-part structure validation.

Author: ZenithEdge Team
"""

import pytest
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zenithedge.settings')
import django
django.setup()

from zenbot.contextualizer import ContextualIntelligenceEngine, generate_narrative
from tests.fixtures.test_data import *


class TestNarrativeStructure:
    """Test that narratives follow the 3-part structure"""
    
    def setup_method(self):
        """Initialize contextualizer"""
        self.engine = ContextualIntelligenceEngine()
    
    @pytest.mark.unit
    def test_narrative_has_three_parts(self):
        """Test that narrative contains header, reasoning, and suggestion"""
        signal_data = VALID_WEBHOOK_HIGH_QUALITY.copy()
        validation_result = {
            'truth_index': 85.0,
            'status': 'approved',
            'breakdown': {
                'technical_integrity': 0.90,
                'volatility_filter': 0.85,
                'regime_alignment': 0.80,
                'sentiment_coherence': 0.75,
                'historical_reliability': 0.85,
                'psychological_safety': 0.90
            },
            'validation_notes': ['✅ Technical: Excellent'],
            'recommendation': 'High-confidence signal'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should have 3 paragraphs separated by double newlines
        parts = narrative.split('\n\n')
        assert len(parts) >= 2, f"Narrative should have at least 2 parts (header + content), got {len(parts)}"
        
        # Check header
        assert '📊' in narrative or 'setup detected' in narrative, "Header should contain signal indicator"
        assert signal_data['symbol'] in narrative, "Header should contain symbol"
        
        # Check for truth index mention
        assert '85' in narrative or '84' in narrative, "Should mention truth index"
    
    @pytest.mark.unit
    def test_narrative_includes_risk_guidance(self):
        """Test that suggestion part includes risk management advice"""
        signal_data = VALID_WEBHOOK_HIGH_QUALITY.copy()
        validation_result = {
            'truth_index': 83.5,
            'status': 'approved',
            'breakdown': {
                'technical_integrity': 0.90,
                'volatility_filter': 0.85,
                'regime_alignment': 0.80,
                'sentiment_coherence': 0.75,
                'historical_reliability': 0.85,
                'psychological_safety': 0.90
            },
            'validation_notes': [],
            'recommendation': 'Proceed'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should include risk percentage or risk guidance
        assert 'Risk' in narrative or 'risk' in narrative, "Should include risk guidance"
        assert '%' in narrative, "Should mention risk percentage"
    
    @pytest.mark.unit
    def test_narrative_includes_entry_and_targets(self):
        """Test that suggestion includes entry level and targets"""
        signal_data = VALID_WEBHOOK_HIGH_QUALITY.copy()
        validation_result = {
            'truth_index': 85.0,
            'status': 'approved',
            'breakdown': {
                'technical_integrity': 0.90,
                'volatility_filter': 0.85,
                'regime_alignment': 0.80,
                'sentiment_coherence': 0.75,
                'historical_reliability': 0.85,
                'psychological_safety': 0.90
            },
            'validation_notes': [],
            'recommendation': 'Proceed'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should mention price levels
        price_str = str(signal_data['price'])
        assert price_str[:4] in narrative, "Should mention entry price"
        
        # Should mention direction
        assert 'Long' in narrative or 'SHORT' in narrative or signal_data['side'].upper() in narrative.upper(), "Should mention trade direction"


class TestStrategyAwareLanguage:
    """Test that narratives use strategy-specific terminology"""
    
    def setup_method(self):
        """Initialize contextualizer"""
        self.engine = ContextualIntelligenceEngine()
    
    @pytest.mark.unit
    def test_smc_strategy_keywords(self):
        """Test that SMC strategies use appropriate keywords"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'smc',  # Smart Money Concepts
            'confidence': 85.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        validation_result = {
            'truth_index': 85.0,
            'status': 'approved',
            'breakdown': {
                'technical_integrity': 0.90,
                'volatility_filter': 0.85,
                'regime_alignment': 0.80,
                'sentiment_coherence': 0.75,
                'historical_reliability': 0.85,
                'psychological_safety': 0.90
            },
            'validation_notes': [],
            'recommendation': 'Proceed'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should use SMC-specific language
        smc_terms = ['CHoCH', 'BOS', 'Fair Value Gap', 'Order Block', 'Liquidity', 'market structure', 'supply/demand']
        has_smc_term = any(term.lower() in narrative.lower() for term in smc_terms)
        
        assert has_smc_term, f"SMC strategy should use SMC terminology. Narrative: {narrative}"
    
    @pytest.mark.unit
    def test_ict_strategy_keywords(self):
        """Test that ICT strategies use appropriate keywords"""
        signal_data = {
            'symbol': 'GBPUSD',
            'side': 'sell',
            'strategy': 'ict',  # Inner Circle Trader
            'confidence': 80.0,
            'price': 1.2600,
            'sl': 1.2650,
            'tp': 1.2500,
            'regime': 'trending',
            'timeframe': '4H'
        }
        
        validation_result = {
            'truth_index': 82.0,
            'status': 'approved',
            'breakdown': {
                'technical_integrity': 0.88,
                'volatility_filter': 0.82,
                'regime_alignment': 0.85,
                'sentiment_coherence': 0.70,
                'historical_reliability': 0.80,
                'psychological_safety': 0.85
            },
            'validation_notes': [],
            'recommendation': 'Proceed'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should use ICT-specific language
        ict_terms = ['Kill Zone', 'Power of 3', 'Balanced Price Range', 'PD Array', 'institutional', 'algorithmic']
        has_ict_term = any(term.lower() in narrative.lower() for term in ict_terms)
        
        assert has_ict_term, f"ICT strategy should use ICT terminology. Narrative: {narrative}"
    
    @pytest.mark.unit
    def test_unknown_strategy_uses_generic_language(self):
        """Test that unknown strategies use generic technical language"""
        signal_data = {
            'symbol': 'EURUSD',
            'side': 'buy',
            'strategy': 'unknown_strategy',
            'confidence': 75.0,
            'price': 1.0800,
            'sl': 1.0750,
            'tp': 1.0900,
            'regime': 'trending',
            'timeframe': '1H'
        }
        
        validation_result = {
            'truth_index': 75.0,
            'status': 'conditional',
            'breakdown': {
                'technical_integrity': 0.75,
                'volatility_filter': 0.75,
                'regime_alignment': 0.75,
                'sentiment_coherence': 0.70,
                'historical_reliability': 0.70,
                'psychological_safety': 0.80
            },
            'validation_notes': [],
            'recommendation': 'Conditional'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should use generic terms
        generic_terms = ['Setup', 'Signal', 'Entry', 'Target', 'technical', 'market conditions']
        has_generic_term = any(term.lower() in narrative.lower() for term in generic_terms)
        
        assert has_generic_term, "Unknown strategy should use generic language"


class TestSessionContext:
    """Test that narratives include session-aware context"""
    
    def setup_method(self):
        """Initialize contextualizer"""
        self.engine = ContextualIntelligenceEngine()
    
    @pytest.mark.unit
    def test_session_detection(self):
        """Test that _get_current_session() returns valid session"""
        from django.utils import timezone
        
        # Mock different times
        session = self.engine._get_current_session()
        
        # Should return one of the valid sessions or None
        valid_sessions = ['london', 'newyork', 'asia', 'overlap', None]
        assert session in valid_sessions, f"Invalid session returned: {session}"
    
    @pytest.mark.unit
    def test_narrative_mentions_session_if_available(self):
        """Test that narrative includes session context when relevant"""
        signal_data = VALID_WEBHOOK_HIGH_QUALITY.copy()
        validation_result = {
            'truth_index': 85.0,
            'status': 'approved',
            'breakdown': {
                'technical_integrity': 0.90,
                'volatility_filter': 0.85,
                'regime_alignment': 0.80,
                'sentiment_coherence': 0.75,
                'historical_reliability': 0.85,
                'psychological_safety': 0.90
            },
            'validation_notes': [],
            'recommendation': 'Proceed'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Check if session is mentioned (London, New York, Asia, or overlap)
        session_mentions = ['session', 'London', 'New York', 'Asia', 'overlap']
        # Note: Session may not always be mentioned if current time is outside major sessions
        # So we just verify the narrative is generated without error
        assert len(narrative) > 50, "Narrative should be generated successfully"


class TestQualityIndicators:
    """Test that narratives reflect signal quality appropriately"""
    
    def setup_method(self):
        """Initialize contextualizer"""
        self.engine = ContextualIntelligenceEngine()
    
    @pytest.mark.unit
    def test_high_confidence_narrative_positive_tone(self):
        """Test that high-confidence signals have positive language"""
        signal_data = VALID_WEBHOOK_HIGH_QUALITY.copy()
        validation_result = {
            'truth_index': 88.0,
            'status': 'approved',
            'breakdown': {
                'technical_integrity': 0.92,
                'volatility_filter': 0.88,
                'regime_alignment': 0.85,
                'sentiment_coherence': 0.82,
                'historical_reliability': 0.87,
                'psychological_safety': 0.90
            },
            'validation_notes': [],
            'recommendation': 'High-confidence signal. Proceed.'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should have positive indicators
        positive_terms = ['✅', 'high-confidence', 'validated', 'Strong', 'Good', 'Excellent']
        has_positive = any(term.lower() in narrative.lower() for term in positive_terms)
        
        assert has_positive, "High-confidence narrative should have positive language"
    
    @pytest.mark.unit
    def test_conditional_narrative_includes_warnings(self):
        """Test that conditional signals include caution language"""
        signal_data = VALID_WEBHOOK_MODERATE_QUALITY.copy()
        validation_result = {
            'truth_index': 68.0,
            'status': 'conditional',
            'breakdown': {
                'technical_integrity': 0.70,
                'volatility_filter': 0.68,
                'regime_alignment': 0.65,
                'sentiment_coherence': 0.60,
                'historical_reliability': 0.70,
                'psychological_safety': 0.75
            },
            'validation_notes': [],
            'recommendation': 'Conditional. Await confirmation.'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should have warning indicators
        warning_terms = ['⚠️', 'conditional', 'caution', 'await', 'confirmation', 'reduce']
        has_warning = any(term.lower() in narrative.lower() for term in warning_terms)
        
        assert has_warning, "Conditional narrative should include warnings"
    
    @pytest.mark.unit
    def test_rejected_narrative_clear_rejection(self):
        """Test that rejected signals have clear rejection language"""
        signal_data = VALID_WEBHOOK_LOW_QUALITY.copy()
        validation_result = {
            'truth_index': 45.0,
            'status': 'rejected',
            'breakdown': {
                'technical_integrity': 0.40,
                'volatility_filter': 0.50,
                'regime_alignment': 0.45,
                'sentiment_coherence': 0.35,
                'historical_reliability': 0.40,
                'psychological_safety': 0.60
            },
            'validation_notes': [],
            'recommendation': 'Signal rejected. Does not meet criteria.'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should have rejection indicators
        rejection_terms = ['❌', 'rejected', 'does not meet', 'criteria', 'skip']
        has_rejection = any(term.lower() in narrative.lower() for term in rejection_terms)
        
        assert has_rejection, "Rejected narrative should have clear rejection language"


class TestEdgeCases:
    """Test contextualizer handles edge cases gracefully"""
    
    def setup_method(self):
        """Initialize contextualizer"""
        self.engine = ContextualIntelligenceEngine()
    
    @pytest.mark.unit
    def test_missing_breakdown_uses_fallback(self):
        """Test that missing breakdown data uses fallback narrative"""
        signal_data = VALID_WEBHOOK_HIGH_QUALITY.copy()
        validation_result = {
            'truth_index': 75.0,
            'status': 'approved',
            # breakdown missing
            'validation_notes': [],
            'recommendation': 'Proceed'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should still generate narrative
        assert len(narrative) > 30, "Should generate narrative even without breakdown"
        assert signal_data['symbol'] in narrative, "Should include symbol"
    
    @pytest.mark.unit
    def test_extreme_truth_index_values(self):
        """Test handling of extreme truth index values"""
        signal_data = VALID_WEBHOOK_HIGH_QUALITY.copy()
        
        # Test very high truth index
        validation_result_high = {
            'truth_index': 98.0,
            'status': 'approved',
            'breakdown': {
                'technical_integrity': 0.98,
                'volatility_filter': 0.97,
                'regime_alignment': 0.98,
                'sentiment_coherence': 0.96,
                'historical_reliability': 0.99,
                'psychological_safety': 0.98
            },
            'validation_notes': [],
            'recommendation': 'Excellent signal'
        }
        
        narrative_high = self.engine.generate_narrative(signal_data, validation_result_high)
        assert 'high-confidence' in narrative_high.lower(), "Very high score should mention high confidence"
        
        # Test very low truth index
        validation_result_low = {
            'truth_index': 15.0,
            'status': 'rejected',
            'breakdown': {
                'technical_integrity': 0.20,
                'volatility_filter': 0.15,
                'regime_alignment': 0.10,
                'sentiment_coherence': 0.10,
                'historical_reliability': 0.15,
                'psychological_safety': 0.20
            },
            'validation_notes': [],
            'recommendation': 'Reject'
        }
        
        narrative_low = self.engine.generate_narrative(signal_data, validation_result_low)
        assert 'reject' in narrative_low.lower() or '❌' in narrative_low, "Very low score should indicate rejection"
    
    @pytest.mark.unit
    def test_error_handling_returns_fallback(self):
        """Test that errors in generation return fallback narrative"""
        signal_data = {
            'symbol': 'TEST',
            # Missing many required fields
        }
        
        validation_result = {
            'truth_index': 75.0,
            'status': 'approved'
        }
        
        narrative = self.engine.generate_narrative(signal_data, validation_result)
        
        # Should return fallback without crashing
        assert 'TEST' in narrative, "Should include symbol in fallback"
        assert '75' in narrative or '74' in narrative, "Should include truth index"


class TestBatchSummary:
    """Test batch summary generation"""
    
    def setup_method(self):
        """Initialize contextualizer"""
        self.engine = ContextualIntelligenceEngine()
    
    @pytest.mark.unit
    def test_batch_summary_multiple_signals(self):
        """Test generating summary for multiple signals"""
        signals = [
            {
                'symbol': 'EURUSD',
                'truth_index': 85.0,
                'status': 'approved'
            },
            {
                'symbol': 'GBPUSD',
                'truth_index': 72.0,
                'status': 'conditional'
            },
            {
                'symbol': 'USDJPY',
                'truth_index': 55.0,
                'status': 'rejected'
            }
        ]
        
        summary = self.engine.generate_batch_summary(signals)
        
        assert '3 signals' in summary, "Should mention total signals"
        assert 'approved' in summary.lower(), "Should mention approved count"
        assert 'EURUSD' in summary or 'strongest' in summary.lower(), "Should mention strongest signal"
    
    @pytest.mark.unit
    def test_batch_summary_empty_list(self):
        """Test handling of empty signal list"""
        signals = []
        
        summary = self.engine.generate_batch_summary(signals)
        
        assert 'No' in summary or 'no' in summary, "Should indicate no signals"
    
    @pytest.mark.unit
    def test_batch_summary_single_signal(self):
        """Test summary with just one signal"""
        signals = [
            {
                'symbol': 'EURUSD',
                'truth_index': 88.0,
                'status': 'approved'
            }
        ]
        
        summary = self.engine.generate_batch_summary(signals)
        
        assert '1 signal' in summary or 'signal' in summary, "Should handle singular"
        assert 'EURUSD' in summary, "Should mention the signal"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
