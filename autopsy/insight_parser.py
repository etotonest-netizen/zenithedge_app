"""
Zenith Market Analyst - Insight Parser

Parses Pine Script metadata and structures it for AI processing.
No external APIs - purely internal data transformation.
"""
import json
from typing import Dict, Any, List
from datetime import datetime
from django.utils import timezone


class InsightParser:
    """
    Parse raw Pine Script metadata into structured insight data
    """
    
    def __init__(self):
        self.required_fields = [
            'regime', 'structure', 'momentum', 'volume_state', 
            'session', 'expected_behavior', 'strength'
        ]
    
    def parse(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw Pine Script JSON into validated insight metadata
        
        Args:
            raw_data: Dictionary from Pine Script alert webhook
            
        Returns:
            Structured insight metadata ready for AI processing
        """
        # Validate required fields
        self._validate(raw_data)
        
        # Extract and normalize core fields
        metadata = {
            'symbol': raw_data.get('symbol', 'UNKNOWN').upper(),
            'timeframe': raw_data.get('timeframe', '1H'),
            'timestamp': self._parse_timestamp(raw_data.get('timestamp')),
            
            # Market state
            'regime': self._normalize_regime(raw_data.get('regime')),
            'structure': self._normalize_structure(raw_data.get('structure')),
            'momentum': self._normalize_momentum(raw_data.get('momentum')),
            'volume_state': self._normalize_volume(raw_data.get('volume_state')),
            'session': self._normalize_session(raw_data.get('session')),
            
            # Context
            'expected_behavior': raw_data.get('expected_behavior', ''),
            'strength': int(raw_data.get('strength', 0)),
            'risk_notes': raw_data.get('risk_notes', []),
            
            # Raw data for reference
            'raw_metadata': raw_data
        }
        
        return metadata
    
    def _validate(self, data: Dict[str, Any]) -> None:
        """Validate required fields are present"""
        missing = [field for field in self.required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
    
    def _parse_timestamp(self, timestamp_value) -> datetime:
        """Convert timestamp to datetime object"""
        if isinstance(timestamp_value, datetime):
            return timestamp_value
        
        if isinstance(timestamp_value, str):
            try:
                # Try ISO format
                return datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
            except:
                pass
            
            try:
                # Try Unix timestamp as string
                return datetime.fromtimestamp(int(timestamp_value), tz=timezone.utc)
            except:
                pass
        
        if isinstance(timestamp_value, (int, float)):
            # Unix timestamp
            return datetime.fromtimestamp(timestamp_value, tz=timezone.utc)
        
        # Default to now if parsing fails
        return timezone.now()
    
    def _normalize_regime(self, value: str) -> str:
        """Normalize regime value to match model choices"""
        if not value:
            return 'unknown'
        
        value = value.lower().strip()
        
        mapping = {
            'trending': 'trending',
            'trend': 'trending',
            'ranging': 'ranging',
            'range': 'ranging',
            'volatile': 'volatile',
            'volatility': 'volatile',
            'consolidation': 'consolidation',
            'consolidating': 'consolidation',
        }
        
        return mapping.get(value, 'unknown')
    
    def _normalize_structure(self, value: str) -> str:
        """Normalize structure value to match model choices"""
        if not value:
            return 'none'
        
        value = value.lower().strip()
        
        mapping = {
            'bos': 'bos',
            'break of structure': 'bos',
            'choch': 'choch',
            'change of character': 'choch',
            'pullback': 'pullback',
            'liquidity sweep': 'liquidity_sweep',
            'sweep': 'liquidity_sweep',
            'fvg': 'fvg',
            'fair value gap': 'fvg',
            'ob': 'order_block',
            'order block': 'order_block',
            'orderblock': 'order_block',
            'eqh': 'eqh',
            'equal highs': 'eqh',
            'eql': 'eql',
            'equal lows': 'eql',
            'compression': 'compression',
            'none': 'none',
            'no clear structure': 'none',
        }
        
        return mapping.get(value, 'none')
    
    def _normalize_momentum(self, value: str) -> str:
        """Normalize momentum value"""
        if not value:
            return 'neutral'
        
        value = value.lower().strip()
        
        mapping = {
            'increasing': 'increasing',
            'up': 'increasing',
            'rising': 'increasing',
            'decreasing': 'decreasing',
            'down': 'decreasing',
            'falling': 'decreasing',
            'diverging': 'diverging',
            'divergence': 'diverging',
            'neutral': 'neutral',
            'flat': 'neutral',
        }
        
        return mapping.get(value, 'neutral')
    
    def _normalize_volume(self, value: str) -> str:
        """Normalize volume state"""
        if not value:
            return 'normal'
        
        value = value.lower().strip()
        
        mapping = {
            'spike': 'spike',
            'high': 'spike',
            'elevated': 'spike',
            'drop': 'drop',
            'low': 'drop',
            'thin': 'drop',
            'normal': 'normal',
            'average': 'normal',
        }
        
        return mapping.get(value, 'normal')
    
    def _normalize_session(self, value: str) -> str:
        """Normalize trading session"""
        if not value:
            return 'off'
        
        value = value.lower().strip()
        
        mapping = {
            'london': 'london',
            'ldn': 'london',
            'new york': 'newyork',
            'ny': 'newyork',
            'newyork': 'newyork',
            'asia': 'asia',
            'asian': 'asia',
            'tokyo': 'asia',
            'off': 'off',
            'off-session': 'off',
        }
        
        return mapping.get(value, 'off')
    
    def extract_chart_labels(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """
        Extract display-ready labels for chart overlay
        
        Returns dict suitable for TradingView label display
        """
        labels = {}
        
        # Structure tag
        if metadata.get('structure') and metadata['structure'] != 'none':
            labels['structure'] = self._structure_to_label(metadata['structure'])
        
        # Regime tag
        if metadata.get('regime') and metadata['regime'] != 'unknown':
            labels['regime'] = metadata['regime'].title()
        
        # Momentum tag
        if metadata.get('momentum') and metadata['momentum'] != 'neutral':
            labels['momentum'] = self._momentum_to_label(metadata['momentum'])
        
        # Volume tag
        if metadata.get('volume_state') and metadata['volume_state'] != 'normal':
            labels['volume'] = self._volume_to_label(metadata['volume_state'])
        
        return labels
    
    def _structure_to_label(self, structure: str) -> str:
        """Convert structure code to display label"""
        mapping = {
            'bos': 'BOS',
            'choch': 'CHoCH',
            'pullback': 'Pullback',
            'liquidity_sweep': 'Sweep',
            'fvg': 'FVG',
            'order_block': 'OB',
            'eqh': 'EQH',
            'eql': 'EQL',
            'compression': 'Compression',
        }
        return mapping.get(structure, structure.upper())
    
    def _momentum_to_label(self, momentum: str) -> str:
        """Convert momentum code to display label"""
        mapping = {
            'increasing': 'Momentum ↑',
            'decreasing': 'Momentum ↓',
            'diverging': 'Divergence',
        }
        return mapping.get(momentum, momentum.title())
    
    def _volume_to_label(self, volume: str) -> str:
        """Convert volume state to display label"""
        mapping = {
            'spike': 'Volume Spike',
            'drop': 'Low Volume',
        }
        return mapping.get(volume, volume.title())
    
    def calculate_context_score(self, metadata: Dict[str, Any]) -> int:
        """
        Calculate preliminary context quality score (0-100)
        Used as input for full insight scoring
        """
        score = 0
        
        # Structure clarity (+30)
        if metadata.get('structure') and metadata['structure'] != 'none':
            score += 30
        
        # Regime identification (+20)
        if metadata.get('regime') and metadata['regime'] != 'unknown':
            score += 20
        
        # Momentum clarity (+15)
        if metadata.get('momentum') and metadata['momentum'] != 'neutral':
            score += 15
        
        # Session validity (+15)
        if metadata.get('session') and metadata['session'] != 'off':
            score += 15
        
        # Strength value (+20, scaled)
        strength = metadata.get('strength', 0)
        score += int((strength / 100) * 20)
        
        return min(100, score)
    
    def build_risk_summary(self, risk_notes: List[str]) -> str:
        """
        Build human-readable risk summary from risk_notes array
        """
        if not risk_notes:
            return "Normal trading conditions"
        
        if len(risk_notes) == 1:
            return risk_notes[0]
        
        if len(risk_notes) == 2:
            return f"{risk_notes[0]} and {risk_notes[1].lower()}"
        
        # Multiple risks
        return f"{', '.join(risk_notes[:-1])}, and {risk_notes[-1].lower()}"
