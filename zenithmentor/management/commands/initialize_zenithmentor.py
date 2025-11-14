"""
Management command to initialize badges and seed curriculum
"""
from django.core.management.base import BaseCommand
from zenithmentor.gamification import initialize_default_badges
from zenithmentor.models import Lesson


class Command(BaseCommand):
    help = 'Initialize ZenithMentor with default badges and curriculum structure'
    
    def handle(self, *args, **options):
        self.stdout.write("Initializing ZenithMentor...")
        
        # Create badges
        self.stdout.write("Creating default badges...")
        initialize_default_badges()
        
        # Create curriculum structure (summary only - full lessons would be added via admin)
        self.stdout.write("Creating curriculum structure...")
        self._create_curriculum_outline()
        
        self.stdout.write(self.style.SUCCESS("ZenithMentor initialized!"))
        self.stdout.write("\nNext steps:")
        self.stdout.write("1. Run: python manage.py build_scenario_bank --synthetic --count 50")
        self.stdout.write("2. Add detailed lesson content via Django admin")
        self.stdout.write("3. Run: python manage.py train_ml_models (after collecting data)")
    
    def _create_curriculum_outline(self):
        """Create the 12-week curriculum outline."""
        curriculum = [
            {
                'week': 0,
                'title': 'Foundations: Market Microstructure',
                'category': 'foundation',
                'order': 1,
                'description': 'Learn market basics, order types, and risk fundamentals',
                'difficulty': 1,
            },
            {
                'week': 1,
                'title': 'Trend Trading & Timeframe Alignment',
                'category': 'trend',
                'order': 1,
                'description': 'Moving averages, ADX, and swing structure',
                'difficulty': 2,
            },
            {
                'week': 2,
                'title': 'Breakout Trading Strategy',
                'category': 'breakout',
                'order': 1,
                'description': 'Range detection and volume confirmation',
                'difficulty': 3,
            },
            {
                'week': 3,
                'title': 'Mean Reversion Trading',
                'category': 'mean_reversion',
                'order': 1,
                'description': 'RSI, Bollinger Bands, and reversion plays',
                'difficulty': 3,
            },
            {
                'week': 4,
                'title': 'Volatility Squeeze Strategy',
                'category': 'volatility',
                'order': 1,
                'description': 'Detecting and trading volatility expansion',
                'difficulty': 4,
            },
            {
                'week': 5,
                'title': 'VWAP & Session Bias',
                'category': 'session_bias',
                'order': 1,
                'description': 'VWAP reclaim and ICT kill zones',
                'difficulty': 4,
            },
            {
                'week': 6,
                'title': 'SMC Primer: Order Blocks & Fair Value Gaps',
                'category': 'smc',
                'order': 1,
                'description': 'Introduction to Smart Money Concepts',
                'difficulty': 5,
            },
            {
                'week': 7,
                'title': 'SMC Advanced: Liquidity Sweeps',
                'category': 'smc',
                'order': 1,
                'description': 'Multi-timeframe SMC analysis',
                'difficulty': 6,
            },
            {
                'week': 8,
                'title': 'Scalping & Execution Discipline',
                'category': 'scalping',
                'order': 1,
                'description': 'Fast execution and intraday tactics',
                'difficulty': 5,
            },
            {
                'week': 9,
                'title': 'Supply & Demand Zones',
                'category': 'supply_demand',
                'order': 1,
                'description': 'Zone identification and trade management',
                'difficulty': 5,
            },
            {
                'week': 10,
                'title': 'PropSim Preparation',
                'category': 'prop_prep',
                'order': 1,
                'description': 'Position sizing and challenge rules',
                'difficulty': 6,
            },
            {
                'week': 11,
                'title': 'Mock Prop Challenge',
                'category': 'prop_prep',
                'order': 1,
                'description': 'Graded prop-style simulation',
                'difficulty': 8,
            },
            {
                'week': 12,
                'title': 'Certification Exam',
                'category': 'certification',
                'order': 1,
                'description': 'Final assessment for ZenithMentor certification',
                'difficulty': 9,
            },
        ]
        
        for lesson_data in curriculum:
            lesson, created = Lesson.objects.get_or_create(
                week=lesson_data['week'],
                order=lesson_data['order'],
                defaults={
                    'title': lesson_data['title'],
                    'slug': lesson_data['title'].lower().replace(' ', '-').replace(':', ''),
                    'category': lesson_data['category'],
                    'description': lesson_data['description'],
                    'difficulty': lesson_data['difficulty'],
                    'learning_objectives': "To be added via admin",
                    'theory_content': "# Lesson Content\n\nTo be added via Django admin.",
                    'is_published': True,
                }
            )
            
            if created:
                self.stdout.write(f"  Created lesson: Week {lesson.week} - {lesson.title}")
