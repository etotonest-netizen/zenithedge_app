"""
Management command to train or retrain ML models
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import os
from decimal import Decimal

from zenithmentor.models import ApprenticeProfile, SimulationRun, MLModel
from zenithmentor.adaptive_coach import ApprenticeProfiler, PassPredictor


class Command(BaseCommand):
    help = 'Train or retrain ML models for adaptive coaching'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['profiler', 'pass_predictor', 'all'],
            default='all',
            help='Which model to train',
        )
        parser.add_argument(
            '--min-samples',
            type=int,
            default=50,
            help='Minimum training samples required',
        )
    
    def handle(self, *args, **options):
        model_type = options['model']
        min_samples = options['min_samples']
        
        if model_type in ['profiler', 'all']:
            self._train_profiler(min_samples)
        
        if model_type in ['pass_predictor', 'all']:
            self._train_pass_predictor(min_samples)
        
        self.stdout.write(self.style.SUCCESS("ML models trained successfully!"))
    
    def _train_profiler(self, min_samples):
        """Train apprentice type classifier."""
        self.stdout.write("Training apprentice profiler...")
        
        # Collect training data
        profiles = ApprenticeProfile.objects.exclude(learner_type='undetermined')
        
        if profiles.count() < min_samples:
            self.stdout.write(self.style.WARNING(
                f"Insufficient data: {profiles.count()} < {min_samples}. Skipping profiler."
            ))
            return
        
        training_data = []
        for profile in profiles:
            data = {
                'win_rate': float(profile.win_rate),
                'avg_risk_per_trade': float(profile.avg_risk_per_trade),
                'risk_consistency_score': float(profile.risk_consistency_score),
                'stop_loss_adherence': float(profile.stop_loss_adherence),
                'avg_reward_risk_ratio': float(profile.avg_reward_risk_ratio),
                'discipline_score': float(profile.discipline_score),
                'journaling_quality_score': float(profile.journaling_quality_score),
                'emotional_control_score': float(profile.emotional_control_score),
                'total_scenarios_attempted': profile.total_scenarios_attempted,
                'lessons_completed': profile.lessons_completed,
                'revenge_trade_count': profile.revenge_trade_count,
                'overconfidence_incidents': profile.overconfidence_incidents,
                'learner_type': profile.learner_type,
            }
            training_data.append(data)
        
        # Train model
        profiler = ApprenticeProfiler()
        metrics = profiler.train(training_data)
        
        self.stdout.write(f"  Profiler trained:")
        self.stdout.write(f"    Accuracy: {metrics['accuracy']:.2%}")
        self.stdout.write(f"    Samples: {metrics['training_samples']} train, {metrics['test_samples']} test")
        
        # Save model record
        MLModel.objects.create(
            model_type='apprentice_classifier',
            version=timezone.now().strftime('%Y%m%d'),
            model_file_path=profiler.model_path,
            feature_names=profiler.FEATURE_NAMES,
            training_samples=metrics['training_samples'],
            training_accuracy=Decimal(str(metrics['accuracy'] * 100)),
            is_active=True,
            deployed_at=timezone.now(),
        )
    
    def _train_pass_predictor(self, min_samples):
        """Train pass probability predictor."""
        self.stdout.write("Training pass predictor...")
        
        # Collect training data from completed challenges
        completed_runs = SimulationRun.objects.filter(status='completed')
        
        if completed_runs.count() < min_samples:
            self.stdout.write(self.style.WARNING(
                f"Insufficient data: {completed_runs.count()} < {min_samples}. Skipping predictor."
            ))
            return
        
        training_data = []
        for run in completed_runs:
            profile = run.apprentice
            data = {
                'overall_expectancy': float(profile.overall_expectancy),
                'win_rate': float(profile.win_rate),
                'avg_risk_per_trade': float(profile.avg_risk_per_trade),
                'risk_consistency_score': float(profile.risk_consistency_score),
                'stop_loss_adherence': float(profile.stop_loss_adherence),
                'avg_reward_risk_ratio': float(profile.avg_reward_risk_ratio),
                'max_drawdown': float(profile.max_drawdown),
                'discipline_score': float(profile.discipline_score),
                'journaling_quality_score': float(profile.journaling_quality_score),
                'emotional_control_score': float(profile.emotional_control_score),
                'lessons_completed': profile.lessons_completed,
                'total_scenarios_passed': profile.total_scenarios_passed,
                'total_scenarios_attempted': profile.total_scenarios_attempted,
                'current_difficulty': profile.current_difficulty,
                'passed': 1 if run.passed else 0,
            }
            training_data.append(data)
        
        # Train model
        predictor = PassPredictor()
        metrics = predictor.train(training_data)
        
        self.stdout.write(f"  Pass predictor trained:")
        self.stdout.write(f"    RMSE: {metrics['rmse']:.2f}")
        self.stdout.write(f"    Samples: {metrics['training_samples']} train, {metrics['test_samples']} test")
        
        # Save model record
        MLModel.objects.create(
            model_type='pass_predictor',
            version=timezone.now().strftime('%Y%m%d'),
            model_file_path=predictor.model_path,
            feature_names=predictor.FEATURE_NAMES,
            training_samples=metrics['training_samples'],
            training_accuracy=None,
            training_notes=f"RMSE: {metrics['rmse']:.2f}",
            is_active=True,
            deployed_at=timezone.now(),
        )
