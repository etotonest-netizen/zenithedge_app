"""
Management command to create predefined firm challenge templates
"""
from django.core.management.base import BaseCommand
from propcoach.models import FirmTemplate
from decimal import Decimal


class Command(BaseCommand):
    help = 'Create predefined firm challenge templates (FTMO, Funding Pips, MFF, TFT, etc.)'

    def handle(self, *args, **options):
        templates_created = 0
        templates_data = [
            # FTMO Phase 1
            {
                'firm_name': 'ftmo',
                'phase': 'phase1',
                'template_name': 'FTMO Phase 1 Challenge',
                'description': 'FTMO Phase 1: Achieve 10% profit with strict risk management',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('10.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('10.00'),
                'challenge_duration_days': 30,
                'min_trading_days': 5,
                'min_trade_duration_minutes': 5,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': False,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('5.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'no_hedging': True,
                    'no_martingale': True,
                    'consistency_rule': 'No single day profit > 50% of total profit'
                }
            },
            # FTMO Phase 2
            {
                'firm_name': 'ftmo',
                'phase': 'phase2',
                'template_name': 'FTMO Phase 2 Verification',
                'description': 'FTMO Phase 2: Achieve 5% profit with the same risk rules',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('5.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('10.00'),
                'challenge_duration_days': 60,
                'min_trading_days': 5,
                'min_trade_duration_minutes': 5,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': False,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('5.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'no_hedging': True,
                    'no_martingale': True,
                    'consistency_rule': 'No single day profit > 50% of total profit'
                }
            },
            # Funding Pips Phase 1
            {
                'firm_name': 'funding_pips',
                'phase': 'phase1',
                'template_name': 'Funding Pips Stage 1',
                'description': 'Funding Pips Stage 1: Achieve 10% profit target',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('10.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('10.00'),
                'challenge_duration_days': 30,
                'min_trading_days': 5,
                'min_trade_duration_minutes': 3,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': True,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('10.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'flexible_rules': True,
                    'weekend_trading_allowed': True
                }
            },
            # Funding Pips Phase 2
            {
                'firm_name': 'funding_pips',
                'phase': 'phase2',
                'template_name': 'Funding Pips Stage 2',
                'description': 'Funding Pips Stage 2: Achieve 5% profit target',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('5.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('10.00'),
                'challenge_duration_days': 60,
                'min_trading_days': 5,
                'min_trade_duration_minutes': 3,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': True,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('10.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'flexible_rules': True,
                    'weekend_trading_allowed': True
                }
            },
            # MyForexFunds Phase 1
            {
                'firm_name': 'mff',
                'phase': 'phase1',
                'template_name': 'MyForexFunds Challenge Phase',
                'description': 'MFF Challenge: Achieve 8% profit with 12% max drawdown',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('8.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('12.00'),
                'challenge_duration_days': 30,
                'min_trading_days': 5,
                'min_trade_duration_minutes': 0,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': True,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('10.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'rapid_evaluation': True,
                    'no_min_trade_time': True
                }
            },
            # MyForexFunds Phase 2
            {
                'firm_name': 'mff',
                'phase': 'phase2',
                'template_name': 'MyForexFunds Verification Phase',
                'description': 'MFF Verification: Achieve 5% profit',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('5.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('12.00'),
                'challenge_duration_days': 60,
                'min_trading_days': 5,
                'min_trade_duration_minutes': 0,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': True,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('10.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'rapid_evaluation': True,
                    'no_min_trade_time': True
                }
            },
            # The Funded Trader Phase 1
            {
                'firm_name': 'tft',
                'phase': 'phase1',
                'template_name': 'The Funded Trader Challenge',
                'description': 'TFT Challenge: Achieve 8% profit with 3 min trading days',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('8.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('10.00'),
                'challenge_duration_days': 30,
                'min_trading_days': 3,
                'min_trade_duration_minutes': 0,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': True,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('5.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'easy_entry': True,
                    'only_3_trading_days': True
                }
            },
            # The Funded Trader Phase 2
            {
                'firm_name': 'tft',
                'phase': 'phase2',
                'template_name': 'The Funded Trader Verification',
                'description': 'TFT Verification: Achieve 5% profit',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('5.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('10.00'),
                'challenge_duration_days': 60,
                'min_trading_days': 3,
                'min_trade_duration_minutes': 0,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': True,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('5.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'easy_entry': True,
                    'only_3_trading_days': True
                }
            },
            # FundedNext Phase 1
            {
                'firm_name': 'ftc',
                'phase': 'phase1',
                'template_name': 'FundedNext Challenge Phase',
                'description': 'FundedNext Challenge: Achieve 10% profit',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('10.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('10.00'),
                'challenge_duration_days': 30,
                'min_trading_days': 5,
                'min_trade_duration_minutes': 0,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': True,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('5.00'),
                'profit_split_percent': Decimal('90.00'),
                'custom_rules': {
                    'high_profit_split': True,
                    'no_min_trade_time': True
                }
            },
            # E8 Funding Phase 1
            {
                'firm_name': 'e8',
                'phase': 'phase1',
                'template_name': 'E8 Funding Challenge',
                'description': 'E8 Challenge: Achieve 8% profit with flexible rules',
                'account_size': Decimal('100000.00'),
                'profit_target_percent': Decimal('8.00'),
                'max_daily_drawdown_percent': Decimal('5.00'),
                'max_total_drawdown_percent': Decimal('14.00'),
                'challenge_duration_days': 30,
                'min_trading_days': 3,
                'min_trade_duration_minutes': 0,
                'max_leverage': Decimal('100.00'),
                'allow_weekend_holding': True,
                'allow_news_trading': True,
                'max_position_size_percent': Decimal('10.00'),
                'profit_split_percent': Decimal('80.00'),
                'custom_rules': {
                    'generous_drawdown': True,
                    'low_minimum_days': True
                }
            },
        ]

        for template_data in templates_data:
            # Check if template already exists
            existing = FirmTemplate.objects.filter(
                firm_name=template_data['firm_name'],
                phase=template_data['phase']
            ).first()
            
            if existing:
                self.stdout.write(
                    self.style.WARNING(
                        f"Template already exists: {template_data['template_name']}"
                    )
                )
                continue
            
            # Create new template
            template = FirmTemplate.objects.create(**template_data)
            templates_created += 1
            self.stdout.write(
                self.style.SUCCESS(
                    f"✓ Created: {template.template_name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"\n{'='*50}\n"
                f"Successfully created {templates_created} firm templates!\n"
                f"{'='*50}"
            )
        )
