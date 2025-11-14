"""
Management command to train the ML pass/fail predictor model
"""
from django.core.management.base import BaseCommand
from propcoach.ml_predictor import train_predictor_model


class Command(BaseCommand):
    help = 'Train the ML model to predict prop challenge pass/fail outcomes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='Train on specific user data only'
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        
        if user_id:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                self.stdout.write(f"\nTraining predictor model for user: {user.username}...\n")
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User with ID {user_id} not found'))
                return
        else:
            user = None
            self.stdout.write("\nTraining predictor model on all users' data...\n")
        
        # Train model
        result = train_predictor_model(user=user)
        
        if result['status'] == 'success':
            self.stdout.write(
                self.style.SUCCESS(
                    f"\n{'='*60}\n"
                    f"✅ Model training successful!\n"
                    f"{'='*60}\n"
                    f"Challenges used: {result['challenges_used']}\n"
                    f"Train accuracy: {result['train_accuracy']}%\n"
                    f"Test accuracy: {result['test_accuracy']}%\n"
                    f"ROC AUC: {result['roc_auc']}\n"
                    f"Cross-validation: {result['cv_scores']['mean']}% (±{result['cv_scores']['std']}%)\n"
                    f"\nTop 5 Most Important Features:\n"
                )
            )
            
            for i, feat in enumerate(result['feature_importance'][:5], 1):
                self.stdout.write(f"  {i}. {feat['feature']}: {feat['importance']}")
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nModel saved to: {result['model_path']}\n"
                    f"{'='*60}\n"
                )
            )
            
        elif result['status'] == 'insufficient_data':
            self.stdout.write(
                self.style.WARNING(
                    f"\n⚠️  {result['message']}\n"
                    f"Complete more challenges to train the model.\n"
                )
            )
            
        else:  # error
            self.stdout.write(
                self.style.ERROR(
                    f"\n✗ Model training failed: {result['message']}\n"
                )
            )
