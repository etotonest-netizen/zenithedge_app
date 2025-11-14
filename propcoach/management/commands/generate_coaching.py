"""
Management command to generate coaching feedback for active challenges
"""
from django.core.management.base import BaseCommand
from propcoach.models import PropChallenge
from propcoach.coaching import generate_daily_feedback


class Command(BaseCommand):
    help = 'Generate daily coaching feedback for all active prop challenges'

    def add_arguments(self, parser):
        parser.add_argument(
            '--challenge-id',
            type=str,
            help='Generate feedback for specific challenge ID'
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Generate feedback for specific user ID'
        )

    def handle(self, *args, **options):
        challenge_id = options.get('challenge_id')
        user_id = options.get('user_id')
        
        # Get challenges to process
        if challenge_id:
            challenges = PropChallenge.objects.filter(id=challenge_id, status='active')
        elif user_id:
            challenges = PropChallenge.objects.filter(user_id=user_id, status='active')
        else:
            challenges = PropChallenge.objects.filter(status='active')
        
        challenge_count = challenges.count()
        
        if challenge_count == 0:
            self.stdout.write(
                self.style.WARNING('No active challenges found')
            )
            return
        
        self.stdout.write(
            self.style.SUCCESS(
                f"\nGenerating coaching feedback for {challenge_count} active challenge(s)...\n"
            )
        )
        
        success_count = 0
        error_count = 0
        
        for challenge in challenges:
            try:
                result = generate_daily_feedback(challenge)
                
                if result:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✓ {challenge.user.username} - {challenge.template.template_name}: "
                            f"{result['feedback_count']} insights generated"
                        )
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(
                            f"✗ {challenge.user.username} - Failed to generate feedback"
                        )
                    )
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"✗ {challenge.user.username} - Error: {str(e)}"
                    )
                )
                error_count += 1
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*50}\n"
                f"Coaching feedback generation complete!\n"
                f"Success: {success_count} | Errors: {error_count}\n"
                f"{'='*50}"
            )
        )
