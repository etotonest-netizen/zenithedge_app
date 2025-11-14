"""
Signal Clusterer for Cognition Module
Groups similar trading signals using scikit-learn clustering
"""
import logging
import numpy as np
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

try:
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logger.warning("scikit-learn not available")

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    logger.warning("pandas not available")


class SignalClusterer:
    """
    Clusters trading signals by behavior and performance patterns
    """
    
    def __init__(self, n_clusters: int = 5):
        """
        Initialize signal clusterer
        
        Args:
            n_clusters: Number of clusters to create
        """
        self.n_clusters = n_clusters
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.kmeans = None
    
    def cluster_signals(self, signals_data: List[Dict]) -> Dict:
        """
        Cluster signals and return cluster assignments with metrics
        
        Args:
            signals_data: List of signal dictionaries with features
            
        Returns:
            Dictionary with cluster assignments and metrics
        """
        if not SKLEARN_AVAILABLE or not PANDAS_AVAILABLE or not signals_data:
            return self._get_default_result()
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(signals_data)
            
            # Extract features
            features = self._extract_features(df)
            
            if features is None or len(features) < self.n_clusters:
                return self._get_default_result()
            
            # Scale features
            scaled_features = self.scaler.fit_transform(features)
            
            # Perform clustering
            self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
            cluster_labels = self.kmeans.fit_predict(scaled_features)
            
            # Calculate metrics for each cluster
            cluster_metrics = self._calculate_cluster_metrics(df, cluster_labels)
            
            # Calculate silhouette score (cluster quality)
            if len(set(cluster_labels)) > 1:
                silhouette_avg = silhouette_score(scaled_features, cluster_labels)
            else:
                silhouette_avg = 0.0
            
            return {
                'cluster_labels': cluster_labels.tolist(),
                'cluster_metrics': cluster_metrics,
                'silhouette_score': silhouette_avg,
                'n_clusters': self.n_clusters,
                'feature_names': features.columns.tolist(),
            }
        
        except Exception as e:
            logger.error(f"Clustering error: {e}")
            return self._get_default_result()
    
    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract numerical features from signals for clustering
        """
        feature_cols = []
        
        # Time-based features
        if 'timestamp' in df.columns:
            df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
            df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
            feature_cols.extend(['hour', 'day_of_week'])
        
        # Performance features
        if 'outcome' in df.columns:
            df['was_profitable'] = (df['outcome'] == 'win').astype(int)
            feature_cols.append('was_profitable')
        
        if 'profit_loss' in df.columns:
            feature_cols.append('profit_loss')
        
        if 'risk_reward' in df.columns:
            feature_cols.append('risk_reward')
        
        # Signal features
        if 'confidence' in df.columns:
            feature_cols.append('confidence')
        
        if 'timeframe' in df.columns:
            # Convert timeframe to numeric (minutes)
            timeframe_map = {'1m': 1, '5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440}
            df['timeframe_minutes'] = df['timeframe'].map(timeframe_map).fillna(15)
            feature_cols.append('timeframe_minutes')
        
        # Strategy features
        if 'strategy' in df.columns:
            # One-hot encode strategies
            strategy_dummies = pd.get_dummies(df['strategy'], prefix='strategy')
            df = pd.concat([df, strategy_dummies], axis=1)
            feature_cols.extend(strategy_dummies.columns.tolist())
        
        # Market condition features
        if 'trend_strength' in df.columns:
            feature_cols.append('trend_strength')
        
        if 'volatility' in df.columns:
            feature_cols.append('volatility')
        
        # Extract only available features
        available_features = [col for col in feature_cols if col in df.columns]
        
        if not available_features:
            return None
        
        return df[available_features].fillna(0)
    
    def _calculate_cluster_metrics(self, df: pd.DataFrame, labels: np.ndarray) -> List[Dict]:
        """
        Calculate performance metrics for each cluster
        """
        df['cluster'] = labels
        metrics = []
        
        for cluster_id in range(self.n_clusters):
            cluster_data = df[df['cluster'] == cluster_id]
            
            if len(cluster_data) == 0:
                continue
            
            # Calculate metrics
            signal_count = len(cluster_data)
            
            # Win rate
            if 'outcome' in cluster_data.columns:
                wins = (cluster_data['outcome'] == 'win').sum()
                win_rate = wins / signal_count if signal_count > 0 else 0.5
            else:
                win_rate = 0.5
            
            # Average profit factor
            if 'profit_loss' in cluster_data.columns:
                profits = cluster_data[cluster_data['profit_loss'] > 0]['profit_loss'].sum()
                losses = abs(cluster_data[cluster_data['profit_loss'] < 0]['profit_loss'].sum())
                avg_profit_factor = profits / losses if losses > 0 else 1.0
            else:
                avg_profit_factor = 1.0
            
            # Average risk/reward
            if 'risk_reward' in cluster_data.columns:
                avg_rr = cluster_data['risk_reward'].mean()
            else:
                avg_rr = 1.5
            
            # Sharpe ratio (simplified)
            if 'profit_loss' in cluster_data.columns:
                returns = cluster_data['profit_loss']
                sharpe = (returns.mean() / returns.std()) if returns.std() > 0 else 0.0
            else:
                sharpe = 0.0
            
            # Reliability score (composite metric)
            reliability = self._calculate_reliability(
                win_rate, avg_profit_factor, sharpe, signal_count
            )
            
            # Common characteristics
            typical_symbols = []
            if 'symbol' in cluster_data.columns:
                typical_symbols = cluster_data['symbol'].value_counts().head(3).index.tolist()
            
            typical_timeframe = ''
            if 'timeframe' in cluster_data.columns:
                typical_timeframe = cluster_data['timeframe'].mode()[0] if len(cluster_data) > 0 else ''
            
            strategy_pattern = ''
            if 'strategy' in cluster_data.columns:
                strategy_pattern = cluster_data['strategy'].mode()[0] if len(cluster_data) > 0 else 'Unknown'
            
            metrics.append({
                'cluster_id': int(cluster_id),
                'signal_count': signal_count,
                'win_rate': float(win_rate),
                'avg_profit_factor': float(avg_profit_factor),
                'avg_risk_reward': float(avg_rr),
                'sharpe_ratio': float(sharpe),
                'reliability_score': float(reliability),
                'typical_symbols': typical_symbols,
                'typical_timeframe': typical_timeframe,
                'strategy_pattern': strategy_pattern,
            })
        
        return metrics
    
    def _calculate_reliability(self, win_rate: float, profit_factor: float, 
                              sharpe: float, sample_size: int) -> float:
        """
        Calculate overall reliability score for a cluster
        """
        # Weight different metrics
        performance_score = (
            win_rate * 0.4 +
            min(profit_factor / 2, 1.0) * 0.3 +
            min((sharpe + 2) / 4, 1.0) * 0.3  # Normalize sharpe
        )
        
        # Penalty for small sample sizes
        sample_confidence = min(sample_size / 50, 1.0)
        
        reliability = performance_score * sample_confidence
        return max(0.0, min(1.0, reliability))
    
    def predict_cluster(self, signal_features: Dict) -> Tuple[int, float]:
        """
        Predict which cluster a new signal belongs to
        
        Args:
            signal_features: Dictionary of signal features
            
        Returns:
            (cluster_id, reliability_score)
        """
        if self.kmeans is None or not SKLEARN_AVAILABLE:
            return 0, 0.5
        
        try:
            # Convert features to array
            feature_array = self._features_to_array(signal_features)
            scaled_features = self.scaler.transform([feature_array])
            
            # Predict cluster
            cluster_id = self.kmeans.predict(scaled_features)[0]
            
            # Get distance to centroid (inverse for confidence)
            distance = self.kmeans.transform(scaled_features)[0][cluster_id]
            confidence = 1.0 / (1.0 + distance)  # Convert distance to confidence
            
            return int(cluster_id), float(confidence)
        
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return 0, 0.5
    
    def _features_to_array(self, features: Dict) -> np.ndarray:
        """Convert feature dictionary to numpy array"""
        # This should match the feature extraction order
        # Simplified version - would need to match training features
        return np.array([
            features.get('confidence', 0.5),
            features.get('timeframe_minutes', 15),
            features.get('trend_strength', 0.5),
            features.get('volatility', 0.5),
        ])
    
    def _get_default_result(self) -> Dict:
        """Return default result for errors"""
        return {
            'cluster_labels': [],
            'cluster_metrics': [],
            'silhouette_score': 0.0,
            'n_clusters': 0,
            'feature_names': [],
        }


# Convenience function
def cluster_signals(signals_data: List[Dict], n_clusters: int = 5) -> Dict:
    """
    Cluster trading signals
    
    Args:
        signals_data: List of signal dictionaries
        n_clusters: Number of clusters to create
        
    Returns:
        Clustering results
    """
    clusterer = SignalClusterer(n_clusters=n_clusters)
    return clusterer.cluster_signals(signals_data)
