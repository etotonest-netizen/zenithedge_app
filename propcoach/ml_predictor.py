"""
ML Pass/Fail Predictor for PropCoach

Uses scikit-learn to predict challenge success probability based on:
- Current performance metrics
- Trading patterns
- Psychology data
- Historical outcomes
"""

from typing import Dict, Tuple, Optional
import numpy as np
import pandas as pd
from decimal import Decimal
import pickle
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Model storage
MODEL_DIR = Path(__file__).parent / 'ml_models'
MODEL_DIR.mkdir(exist_ok=True)
PREDICTOR_MODEL_PATH = MODEL_DIR / 'pass_fail_predictor.pkl'
PREDICTOR_SCALER_PATH = MODEL_DIR / 'pass_fail_scaler.pkl'


def extract_challenge_features(challenge) -> Dict[str, float]:
    """
    Extract numerical features from a PropChallenge for ML prediction.
    
    Args:
        challenge: PropChallenge instance
        
    Returns:
        Dict of features
    """
    template = challenge.template
    
    features = {
        # Progress metrics (0-1 scale)
        'profit_progress_ratio': float(challenge.total_profit_loss / template.get_profit_target_amount()) if template.get_profit_target_amount() > 0 else 0,
        'time_elapsed_ratio': challenge.days_elapsed / template.challenge_duration_days if template.challenge_duration_days > 0 else 0,
        'trading_days_ratio': challenge.trading_days_count / template.min_trading_days if template.min_trading_days > 0 else 0,
        
        # Performance metrics
        'win_rate': challenge.win_rate / 100.0,  # Normalize to 0-1
        'total_trades': min(challenge.total_trades / 50.0, 1.0),  # Normalize, cap at 50
        'trades_per_day': (challenge.total_trades / max(challenge.days_elapsed, 1)) / 5.0,  # Normalize, cap at 5/day
        
        # Risk metrics (0-1 scale, 1 = at limit)
        'daily_dd_ratio': float(challenge.current_daily_drawdown / template.get_max_daily_loss()) if template.get_max_daily_loss() > 0 else 0,
        'total_dd_ratio': float(challenge.current_total_drawdown / template.get_max_total_loss()) if template.get_max_total_loss() > 0 else 0,
        'max_daily_dd_ratio': float(challenge.max_daily_drawdown_reached / template.get_max_daily_loss()) if template.get_max_daily_loss() > 0 else 0,
        'max_total_dd_ratio': float(challenge.max_total_drawdown_reached / template.get_max_total_loss()) if template.get_max_total_loss() > 0 else 0,
        
        # Discipline metrics
        'violation_count': min(challenge.violation_count / 5.0, 1.0),  # Normalize, cap at 5
        'has_violations': 1.0 if challenge.violation_count > 0 else 0.0,
        
        # Balance metrics
        'balance_growth': float((challenge.current_balance - challenge.initial_balance) / challenge.initial_balance) if challenge.initial_balance > 0 else 0,
        'peak_balance_ratio': float(challenge.peak_balance / challenge.initial_balance) if challenge.initial_balance > 0 else 1.0,
        
        # Funding readiness
        'readiness_score': float(challenge.funding_readiness_score) / 100.0,  # Normalize to 0-1
        
        # Challenge difficulty
        'profit_target_pct': float(template.profit_target_percent) / 10.0,  # Normalize (typically 5-10%)
        'max_dd_pct': float(template.max_total_drawdown_percent) / 10.0,  # Normalize
        
        # Firm type (one-hot encoding)
        'is_ftmo': 1.0 if template.firm_name == 'ftmo' else 0.0,
        'is_funding_pips': 1.0 if template.firm_name == 'funding_pips' else 0.0,
        'is_mff': 1.0 if template.firm_name == 'mff' else 0.0,
        'is_tft': 1.0 if template.firm_name == 'tft' else 0.0,
        
        # Phase
        'is_phase1': 1.0 if template.phase == 'phase1' else 0.0,
        'is_phase2': 1.0 if template.phase == 'phase2' else 0.0,
    }
    
    return features


def train_predictor_model(user=None) -> Dict:
    """
    Train the pass/fail predictor model using historical challenge data.
    
    Args:
        user: Optional user to train on specific user data (None = all users)
        
    Returns:
        Dict with training results
    """
    from propcoach.models import PropChallenge
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import classification_report, roc_auc_score
    
    try:
        # Get completed challenges
        query = PropChallenge.objects.filter(status__in=['passed', 'failed'])
        if user:
            query = query.filter(user=user)
        
        challenges = list(query)
        
        if len(challenges) < 20:
            return {
                'status': 'insufficient_data',
                'message': f'Need at least 20 completed challenges for training, found {len(challenges)}',
                'challenges_found': len(challenges)
            }
        
        # Extract features and labels
        feature_list = []
        labels = []
        
        for challenge in challenges:
            features = extract_challenge_features(challenge)
            feature_list.append(features)
            labels.append(1 if challenge.status == 'passed' else 0)
        
        # Convert to DataFrame
        df = pd.DataFrame(feature_list)
        X = df.values
        y = np.array(labels)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train model - use Gradient Boosting for better performance
        model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        logger.info("Training Gradient Boosting classifier...")
        model.fit(X_train_scaled, y_train)
        
        # Evaluate
        train_score = model.score(X_train_scaled, y_train)
        test_score = model.score(X_test_scaled, y_test)
        
        # Get predictions for more metrics
        y_pred = model.predict(X_test_scaled)
        y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
        
        # Calculate metrics
        roc_auc = roc_auc_score(y_test, y_pred_proba)
        
        # Feature importance
        feature_names = list(df.columns)
        importance = model.feature_importances_
        feature_importance = sorted(
            zip(feature_names, importance),
            key=lambda x: x[1],
            reverse=True
        )[:10]  # Top 10
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
        
        # Save model and scaler
        with open(PREDICTOR_MODEL_PATH, 'wb') as f:
            pickle.dump(model, f)
        
        with open(PREDICTOR_SCALER_PATH, 'wb') as f:
            pickle.dump(scaler, f)
        
        logger.info(f"✅ Predictor model trained and saved!")
        logger.info(f"   Train accuracy: {train_score:.2%}")
        logger.info(f"   Test accuracy: {test_score:.2%}")
        logger.info(f"   ROC AUC: {roc_auc:.3f}")
        
        return {
            'status': 'success',
            'challenges_used': len(challenges),
            'train_accuracy': round(train_score * 100, 2),
            'test_accuracy': round(test_score * 100, 2),
            'roc_auc': round(roc_auc, 3),
            'cv_scores': {
                'mean': round(cv_scores.mean() * 100, 2),
                'std': round(cv_scores.std() * 100, 2)
            },
            'feature_importance': [
                {'feature': name, 'importance': round(imp, 3)}
                for name, imp in feature_importance
            ],
            'model_path': str(PREDICTOR_MODEL_PATH),
            'scaler_path': str(PREDICTOR_SCALER_PATH)
        }
        
    except Exception as e:
        logger.error(f"Model training failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


def load_predictor_model() -> Tuple[Optional[object], Optional[object]]:
    """Load trained predictor model and scaler from disk."""
    try:
        with open(PREDICTOR_MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        
        with open(PREDICTOR_SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        
        return model, scaler
    except FileNotFoundError:
        logger.warning("Predictor model not found. Train it first using train_predictor_model()")
        return None, None
    except Exception as e:
        logger.error(f"Failed to load predictor model: {e}")
        return None, None


def predict_challenge_outcome(challenge) -> Dict:
    """
    Predict the probability of passing a challenge.
    
    Args:
        challenge: PropChallenge instance (active)
        
    Returns:
        Dict with prediction results
    """
    try:
        # Load model
        model, scaler = load_predictor_model()
        
        if model is None or scaler is None:
            # Fallback to rule-based prediction
            return rule_based_prediction(challenge)
        
        # Extract features
        features = extract_challenge_features(challenge)
        feature_vector = np.array([list(features.values())])
        
        # Scale features
        feature_vector_scaled = scaler.transform(feature_vector)
        
        # Get prediction probability
        pass_prob = model.predict_proba(feature_vector_scaled)[0][1]
        pass_prob_pct = pass_prob * 100
        
        # Get prediction
        will_pass = pass_prob >= 0.5
        
        # Update challenge with prediction
        challenge.pass_probability = Decimal(str(pass_prob_pct))
        challenge.save(update_fields=['pass_probability'])
        
        # Generate insights
        insights = generate_prediction_insights(challenge, features, pass_prob_pct)
        
        return {
            'status': 'success',
            'pass_probability': round(pass_prob_pct, 2),
            'prediction': 'PASS' if will_pass else 'FAIL',
            'confidence': 'High' if abs(pass_prob - 0.5) > 0.3 else 'Medium' if abs(pass_prob - 0.5) > 0.15 else 'Low',
            'model_type': 'gradient_boosting',
            'insights': insights
        }
        
    except Exception as e:
        logger.error(f"Prediction failed: {e}", exc_info=True)
        return {
            'status': 'error',
            'message': str(e)
        }


def rule_based_prediction(challenge) -> Dict:
    """
    Fallback rule-based prediction when ML model is not available.
    """
    template = challenge.template
    
    score = 50  # Start neutral
    
    # Profit progress (30%)
    profit_progress = challenge.profit_progress_percent
    if profit_progress >= 100:
        score += 30
    elif profit_progress >= 80:
        score += 20
    elif profit_progress >= 50:
        score += 10
    elif profit_progress < 0:
        score -= 20
    
    # Drawdown safety (25%)
    daily_dd_pct = (challenge.current_daily_drawdown / template.get_max_daily_loss() * 100) if template.get_max_daily_loss() > 0 else 0
    total_dd_pct = (challenge.current_total_drawdown / template.get_max_total_loss() * 100) if template.get_max_total_loss() > 0 else 0
    
    if daily_dd_pct < 30 and total_dd_pct < 30:
        score += 25
    elif daily_dd_pct < 60 and total_dd_pct < 60:
        score += 15
    elif daily_dd_pct >= 80 or total_dd_pct >= 80:
        score -= 30
    
    # Violations (20%)
    if challenge.violation_count == 0:
        score += 20
    elif challenge.violation_count <= 2:
        score += 5
    else:
        score -= 20
    
    # Win rate (15%)
    if challenge.win_rate >= 60:
        score += 15
    elif challenge.win_rate >= 50:
        score += 10
    elif challenge.win_rate < 40:
        score -= 15
    
    # Time remaining (10%)
    if challenge.days_remaining >= 10:
        score += 10
    elif challenge.days_remaining <= 3:
        score -= 10
    
    # Clamp score
    pass_prob = max(0, min(100, score))
    
    return {
        'status': 'success',
        'pass_probability': pass_prob,
        'prediction': 'PASS' if pass_prob >= 50 else 'FAIL',
        'confidence': 'Low',
        'model_type': 'rule_based',
        'note': 'Train ML model for better predictions'
    }


def generate_prediction_insights(challenge, features: Dict, pass_prob: float) -> Dict:
    """Generate insights about the prediction."""
    insights = {
        'key_strengths': [],
        'key_risks': [],
        'recommendations': []
    }
    
    # Analyze strengths
    if features['win_rate'] >= 0.6:
        insights['key_strengths'].append(f"Excellent win rate ({features['win_rate']*100:.1f}%)")
    
    if features['violation_count'] == 0:
        insights['key_strengths'].append("Perfect discipline - no violations")
    
    if features['daily_dd_ratio'] < 0.3 and features['total_dd_ratio'] < 0.3:
        insights['key_strengths'].append("Strong risk management - low drawdown")
    
    if features['profit_progress_ratio'] >= 0.8:
        insights['key_strengths'].append("Near profit target")
    
    # Analyze risks
    if features['daily_dd_ratio'] >= 0.7:
        insights['key_risks'].append("High daily drawdown - danger zone")
    
    if features['total_dd_ratio'] >= 0.7:
        insights['key_risks'].append("High total drawdown - at risk")
    
    if features['violation_count'] >= 0.4:  # 2+ violations
        insights['key_risks'].append("Multiple rule violations")
    
    if features['time_elapsed_ratio'] >= 0.8 and features['profit_progress_ratio'] < 0.5:
        insights['key_risks'].append("Running out of time")
    
    if features['win_rate'] < 0.4:
        insights['key_risks'].append("Low win rate")
    
    # Generate recommendations
    if pass_prob >= 80:
        insights['recommendations'].append("You're on track! Maintain discipline")
        insights['recommendations'].append("Protect your gains with conservative trades")
    elif pass_prob >= 60:
        insights['recommendations'].append("Good progress - stay focused")
        insights['recommendations'].append("Avoid unnecessary risks")
    elif pass_prob >= 40:
        insights['recommendations'].append("Critical phase - improve win rate")
        insights['recommendations'].append("Reduce position sizes")
    else:
        insights['recommendations'].append("High risk of failure - consider pausing")
        insights['recommendations'].append("Review your strategy thoroughly")
    
    return insights


def get_prediction_confidence_interval(challenge, n_bootstrap: int = 100) -> Tuple[float, float]:
    """
    Calculate confidence interval for prediction using bootstrap.
    
    Args:
        challenge: PropChallenge instance
        n_bootstrap: Number of bootstrap samples
        
    Returns:
        Tuple of (lower_bound, upper_bound) percentages
    """
    model, scaler = load_predictor_model()
    
    if model is None or scaler is None:
        return (0.0, 100.0)  # Wide interval when no model
    
    features = extract_challenge_features(challenge)
    feature_vector = np.array([list(features.values())])
    feature_vector_scaled = scaler.transform(feature_vector)
    
    predictions = []
    for _ in range(n_bootstrap):
        # Add small random noise to simulate uncertainty
        noisy_features = feature_vector_scaled + np.random.normal(0, 0.05, feature_vector_scaled.shape)
        prob = model.predict_proba(noisy_features)[0][1]
        predictions.append(prob * 100)
    
    predictions = np.array(predictions)
    lower = np.percentile(predictions, 5)  # 5th percentile
    upper = np.percentile(predictions, 95)  # 95th percentile
    
    return (round(lower, 2), round(upper, 2))
