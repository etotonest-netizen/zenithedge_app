"""
Adaptive Coach - ML-powered personalized training
Uses scikit-learn for apprentice profiling and adaptive difficulty
"""
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import joblib
import os
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
from django.conf import settings
from django.utils import timezone


class ApprenticeProfiler:
    """Classifies apprentices into learner types using ML."""
    
    FEATURE_NAMES = [
        'win_rate', 'avg_risk_per_trade', 'risk_consistency_score',
        'stop_loss_adherence', 'avg_reward_risk_ratio', 'discipline_score',
        'journaling_quality_score', 'emotional_control_score',
        'total_scenarios_attempted', 'lessons_completed',
        'revenge_trade_count', 'overconfidence_incidents',
    ]
    
    LEARNER_TYPES = ['analytical', 'intuitive', 'aggressive', 'conservative']
    
    def __init__(self, model_path: Optional[str] = None):
        self.scaler = StandardScaler()
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model_path = model_path or os.path.join(settings.BASE_DIR, 'ml_models', 'apprentice_classifier.pkl')
        
        if os.path.exists(self.model_path):
            self.load_model()
    
    def extract_features(self, apprentice) -> np.array:
        """Extract feature vector from ApprenticeProfile."""
        features = []
        for feat_name in self.FEATURE_NAMES:
            value = getattr(apprentice, feat_name, 0)
            if isinstance(value, Decimal):
                value = float(value)
            features.append(value)
        
        return np.array(features).reshape(1, -1)
    
    def classify(self, apprentice) -> Tuple[str, float]:
        """
        Classify apprentice into learner type.
        
        Returns:
            Tuple of (learner_type, confidence)
        """
        features = self.extract_features(apprentice)
        features_scaled = self.scaler.transform(features)
        
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        confidence = max(probabilities)
        
        return prediction, confidence
    
    def train(self, apprentices_data: List[Dict]) -> Dict:
        """
        Train classifier on historical apprentice data.
        
        Args:
            apprentices_data: List of dicts with features + 'learner_type' label
        
        Returns:
            Training metrics
        """
        X = []
        y = []
        
        for data in apprentices_data:
            features = [data.get(feat, 0) for feat in self.FEATURE_NAMES]
            X.append(features)
            y.append(data['learner_type'])
        
        X = np.array(X)
        y = np.array(y)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Fit scaler
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        # Save model
        self.save_model()
        
        return {
            'accuracy': accuracy,
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_importances': dict(zip(self.FEATURE_NAMES, self.model.feature_importances_)),
        }
    
    def save_model(self):
        """Persist model to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.FEATURE_NAMES,
        }, self.model_path)
    
    def load_model(self):
        """Load model from disk."""
        data = joblib.load(self.model_path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.FEATURE_NAMES = data['feature_names']


class PassPredictor:
    """Predicts probability of apprentice passing certification."""
    
    FEATURE_NAMES = [
        'overall_expectancy', 'win_rate', 'avg_risk_per_trade',
        'risk_consistency_score', 'stop_loss_adherence',
        'avg_reward_risk_ratio', 'max_drawdown',
        'discipline_score', 'journaling_quality_score',
        'emotional_control_score', 'lessons_completed',
        'total_scenarios_passed', 'total_scenarios_attempted',
        'current_difficulty',
    ]
    
    def __init__(self, model_path: Optional[str] = None):
        self.scaler = StandardScaler()
        self.model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.model_path = model_path or os.path.join(settings.BASE_DIR, 'ml_models', 'pass_predictor.pkl')
        
        if os.path.exists(self.model_path):
            self.load_model()
    
    def extract_features(self, apprentice) -> np.array:
        """Extract feature vector."""
        features = []
        for feat_name in self.FEATURE_NAMES:
            value = getattr(apprentice, feat_name, 0)
            if isinstance(value, Decimal):
                value = float(value)
            features.append(value)
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, apprentice) -> float:
        """
        Predict pass probability (0-100).
        
        Returns:
            Probability percentage
        """
        features = self.extract_features(apprentice)
        features_scaled = self.scaler.transform(features)
        
        prediction = self.model.predict(features_scaled)[0]
        
        # Clip to 0-100 range
        return max(0, min(100, prediction))
    
    def train(self, training_data: List[Dict]) -> Dict:
        """
        Train pass predictor.
        
        Args:
            training_data: List of dicts with features + 'passed' (0/1) label
        
        Returns:
            Training metrics
        """
        X = []
        y = []
        
        for data in training_data:
            features = [data.get(feat, 0) for feat in self.FEATURE_NAMES]
            X.append(features)
            y.append(data['passed'] * 100)  # Convert to percentage
        
        X = np.array(X)
        y = np.array(y)
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Fit scaler
        self.scaler.fit(X_train)
        X_train_scaled = self.scaler.transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        mse = mean_squared_error(y_test, y_pred)
        
        # Save
        self.save_model()
        
        return {
            'mse': mse,
            'rmse': np.sqrt(mse),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'feature_importances': dict(zip(self.FEATURE_NAMES, self.model.feature_importances_)),
        }
    
    def save_model(self):
        """Persist model."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.FEATURE_NAMES,
        }, self.model_path)
    
    def load_model(self):
        """Load model."""
        data = joblib.load(self.model_path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.FEATURE_NAMES = data['feature_names']


class DifficultyAdapter:
    """Adapts scenario difficulty based on performance."""
    
    def __init__(self):
        self.target_win_rate = 0.55  # Target 55% win rate
        self.adjustment_threshold = 5  # Scenarios before adjustment
    
    def recommend_difficulty(self, apprentice) -> int:
        """
        Recommend difficulty level (1-10) for next scenario.
        
        Uses recent performance to adapt challenge level.
        """
        current_diff = apprentice.current_difficulty
        
        # Get recent simulation runs
        from .models import SimulationRun
        recent_runs = SimulationRun.objects.filter(
            apprentice=apprentice,
            status='completed'
        ).order_by('-completed_at')[:self.adjustment_threshold]
        
        if recent_runs.count() < self.adjustment_threshold:
            # Not enough data, keep current
            return current_diff
        
        # Calculate recent win rate
        passed = recent_runs.filter(passed=True).count()
        win_rate = passed / recent_runs.count()
        
        # Calculate recent scores
        avg_score = sum(run.overall_score for run in recent_runs) / recent_runs.count()
        
        # Adapt difficulty
        new_diff = current_diff
        
        if win_rate > 0.70 and avg_score > 80:
            # Doing too well, increase difficulty
            new_diff = min(10, current_diff + 1)
        elif win_rate < 0.40 or avg_score < 60:
            # Struggling, decrease difficulty
            new_diff = max(1, current_diff - 1)
        
        return new_diff
    
    def recommend_position_size_limit(self, apprentice, account_balance: Decimal) -> Decimal:
        """
        Recommend max position size based on risk management.
        
        Returns:
            Maximum position size in account currency
        """
        # Base limit on discipline score
        discipline = float(apprentice.discipline_score)
        
        if discipline >= 80:
            max_risk_pct = 0.02  # 2% per trade
        elif discipline >= 60:
            max_risk_pct = 0.015  # 1.5% per trade
        else:
            max_risk_pct = 0.01  # 1% per trade - training wheels
        
        # Also consider recent revenge trades
        if apprentice.revenge_trade_count > 3:
            max_risk_pct *= 0.5  # Cut risk in half if showing revenge trading
        
        return account_balance * Decimal(str(max_risk_pct))


class AdaptiveCoach:
    """Main adaptive coaching system integrating all ML components."""
    
    def __init__(self):
        self.profiler = ApprenticeProfiler()
        self.pass_predictor = PassPredictor()
        self.difficulty_adapter = DifficultyAdapter()
    
    def update_apprentice_profile(self, apprentice):
        """Update apprentice classification and predictions."""
        # Update learner type
        learner_type, confidence = self.profiler.classify(apprentice)
        
        if confidence > 0.6:  # Only update if confident
            apprentice.learner_type = learner_type
        
        # Update pass probability
        apprentice.pass_probability = Decimal(str(self.pass_predictor.predict(apprentice)))
        
        # Update difficulty
        new_diff = self.difficulty_adapter.recommend_difficulty(apprentice)
        apprentice.current_difficulty = new_diff
        
        apprentice.save()
    
    def generate_personalized_feedback(self, simulation_run) -> Dict:
        """
        Generate coaching feedback tailored to apprentice type.
        
        Returns:
            Dict with feedback, strengths, weaknesses, suggestions
        """
        apprentice = simulation_run.apprentice
        learner_type = apprentice.learner_type
        
        feedback_templates = {
            'analytical': {
                'strength': 'Your systematic approach and attention to detail are excellent.',
                'weakness': 'You may be overthinking entries. Trust your analysis.',
                'suggestion': 'Focus on execution speed once your checklist is complete.',
            },
            'intuitive': {
                'strength': 'Your pattern recognition and market feel are strong.',
                'weakness': 'Document your reasoning more thoroughly for consistency.',
                'suggestion': 'Create a written ruleset to codify your intuition.',
            },
            'aggressive': {
                'strength': 'You\'re decisive and confident in your convictions.',
                'weakness': 'Consider reducing position sizes and taking partial profits.',
                'suggestion': 'Practice defensive risk management to preserve capital.',
            },
            'conservative': {
                'strength': 'Your risk management and capital preservation are solid.',
                'weakness': 'You might be missing good opportunities due to hesitation.',
                'suggestion': 'Increase confidence by reviewing past successful trades.',
            },
        }
        
        template = feedback_templates.get(learner_type, feedback_templates['analytical'])
        
        # Analyze performance
        strengths = []
        weaknesses = []
        suggestions = []
        
        # Risk management
        if simulation_run.risk_mgmt_score >= 80:
            strengths.append("Excellent risk management discipline")
        elif simulation_run.risk_mgmt_score < 60:
            weaknesses.append("Risk management needs improvement")
            suggestions.append("Review position sizing rules and always use stop losses")
        
        # Journaling
        if simulation_run.journaling_score >= 75:
            strengths.append("High-quality trade documentation")
        elif simulation_run.journaling_score < 50:
            weaknesses.append("Trade journaling is insufficient")
            suggestions.append("Write detailed pre-trade and post-trade analysis")
        
        # Execution
        if simulation_run.execution_score >= 80:
            strengths.append("Clean execution with minimal slippage")
        elif simulation_run.execution_score < 60:
            weaknesses.append("Execution timing can be improved")
            suggestions.append("Use limit orders and wait for optimal entry points")
        
        # Add learner-type specific feedback
        strengths.append(template['strength'])
        if simulation_run.overall_score < 70:
            weaknesses.append(template['weakness'])
            suggestions.append(template['suggestion'])
        
        feedback_text = self._compile_feedback_text(simulation_run, strengths, weaknesses, suggestions)
        
        return {
            'feedback': feedback_text,
            'strengths': strengths,
            'weaknesses': weaknesses,
            'suggestions': suggestions,
        }
    
    def _compile_feedback_text(self, run, strengths, weaknesses, suggestions) -> str:
        """Compile structured feedback into narrative text."""
        text = f"## Simulation Performance Review\n\n"
        text += f"**Overall Score:** {run.overall_score}/100 - "
        text += "**PASSED** ✓\n\n" if run.passed else "**NEEDS IMPROVEMENT**\n\n"
        
        text += f"### Breakdown\n"
        text += f"- Technical Analysis: {run.technical_score}/100\n"
        text += f"- Risk Management: {run.risk_mgmt_score}/100\n"
        text += f"- Execution: {run.execution_score}/100\n"
        text += f"- Journaling: {run.journaling_score}/100\n"
        text += f"- Discipline: {run.discipline_score}/100\n\n"
        
        if strengths:
            text += "### Strengths\n"
            for s in strengths:
                text += f"- {s}\n"
            text += "\n"
        
        if weaknesses:
            text += "### Areas for Improvement\n"
            for w in weaknesses:
                text += f"- {w}\n"
            text += "\n"
        
        if suggestions:
            text += "### Recommendations\n"
            for s in suggestions:
                text += f"- {s}\n"
            text += "\n"
        
        return text
    
    def should_intervene(self, apprentice, current_trade_data: Dict) -> Tuple[bool, str]:
        """
        Determine if coach should intervene to prevent bad trade.
        
        Returns:
            Tuple of (should_block, reason)
        """
        # Check if in assisted mode
        if apprentice.coaching_mode != 'assisted':
            return False, ""
        
        # Check risk limits
        risk_pct = current_trade_data.get('risk_percentage', 0)
        max_allowed = float(apprentice.max_position_size) / current_trade_data.get('account_balance', 1) * 100
        
        if risk_pct > max_allowed:
            return True, f"Risk {risk_pct:.2f}% exceeds your current limit of {max_allowed:.2f}%"
        
        # Check for revenge trading pattern
        from .models import TradeEntry
        recent_trades = TradeEntry.objects.filter(
            simulation_run__apprentice=apprentice,
            created_at__gte=timezone.now() - timezone.timedelta(hours=1)
        ).order_by('-created_at')[:3]
        
        if len(recent_trades) >= 2:
            recent_losers = [t for t in recent_trades if t.was_winner == False]
            if len(recent_losers) >= 2:
                return True, "Detected potential revenge trading. Take a break and review your plan."
        
        return False, ""


# Singleton instance
adaptive_coach = AdaptiveCoach()
