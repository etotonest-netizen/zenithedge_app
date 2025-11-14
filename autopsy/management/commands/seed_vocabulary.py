"""
Management command to seed VariationVocabulary with 100+ initial variations
Usage: python manage.py seed_vocabulary
"""
from django.core.management.base import BaseCommand
from autopsy.models import VariationVocabulary


class Command(BaseCommand):
    help = 'Seed VariationVocabulary with 100+ initial phrase variations for Zenith Market Analyst'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding Variation Vocabulary...\n')
        
        # Clear existing vocabulary (optional)
        count = VariationVocabulary.objects.count()
        if count > 0:
            self.stdout.write(f'⚠️  Found {count} existing entries. Clearing...')
            VariationVocabulary.objects.all().delete()
        
        created_count = 0
        
        # ========== LIQUIDITY VARIATIONS ==========
        liquidity_entries = [
            {
                'category': 'liquidity',
                'subcategory': 'building',
                'base_phrase': 'liquidity building',
                'variations': [
                    'liquidity building',
                    'liquidity forming',
                    'liquidity accumulating',
                    'resting liquidity observed above',
                    'orders stacking',
                    'liquidity zone forming',
                    'resting orders accumulating',
                    'liquidity pockets developing'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending", "consolidation"]}'
            },
            {
                'category': 'liquidity',
                'subcategory': 'sweeping',
                'base_phrase': 'liquidity swept',
                'variations': [
                    'liquidity swept',
                    'stops triggered',
                    'liquidity collected',
                    'orders executed above',
                    'sweep confirmed',
                    'liquidity grab detected',
                    'stop hunt completed'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending", "volatile"]}'
            },
        ]
        
        # ========== MOMENTUM VARIATIONS ==========
        momentum_entries = [
            {
                'category': 'momentum',
                'subcategory': 'increasing',
                'base_phrase': 'momentum increasing',
                'variations': [
                    'momentum increasing',
                    'momentum accelerating',
                    'momentum climbing',
                    'momentum picking up',
                    'acceleration detected',
                    'pressure building',
                    'buyers stepping in',
                    'momentum strengthening'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending"]}'
            },
            {
                'category': 'momentum',
                'subcategory': 'decreasing',
                'base_phrase': 'momentum decreasing',
                'variations': [
                    'momentum decreasing',
                    'momentum fading',
                    'momentum weakening',
                    'pressure easing',
                    'momentum slowing',
                    'buyers losing interest',
                    'selling pressure emerging'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["ranging", "consolidation"]}'
            },
            {
                'category': 'momentum',
                'subcategory': 'diverging',
                'base_phrase': 'momentum diverging',
                'variations': [
                    'momentum diverging',
                    'divergence forming',
                    'momentum misalignment detected',
                    'price-momentum disconnect',
                    'hidden divergence spotted',
                    'momentum discrepancy noted'
                ],
                'priority': 2,
                'appropriate_for': '{"regime": ["trending", "ranging"]}'
            },
        ]
        
        # ========== STRUCTURE VARIATIONS ==========
        structure_entries = [
            {
                'category': 'structure',
                'subcategory': 'bos',
                'base_phrase': 'Break of Structure',
                'variations': [
                    'Break of Structure validates trend',
                    'BOS confirms shift',
                    'structural break signals change',
                    'key level broken decisively',
                    'structure shift confirmed'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending"]}'
            },
            {
                'category': 'structure',
                'subcategory': 'choch',
                'base_phrase': 'Change of Character',
                'variations': [
                    'Change of Character detected',
                    'CHoCH signals potential reversal',
                    'market character shifting',
                    'behavior change noted'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending", "consolidation"]}'
            },
            {
                'category': 'structure',
                'subcategory': 'pullback',
                'base_phrase': 'pullback forming',
                'variations': [
                    'pullback forming',
                    'retracement in progress',
                    'healthy correction underway',
                    'pullback to key zone',
                    'retest developing',
                    'correction phase'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending"]}'
            },
            {
                'category': 'structure',
                'subcategory': 'order_block',
                'base_phrase': 'order block reaction',
                'variations': [
                    'order block reaction',
                    'institutional zone respected',
                    'OB holding as support',
                    'key zone providing structure',
                    'order block engaged'
                ],
                'priority': 2,
                'appropriate_for': '{"regime": ["trending", "ranging"]}'
            },
        ]
        
        # ========== REGIME VARIATIONS ==========
        regime_entries = [
            {
                'category': 'regime',
                'subcategory': 'trending',
                'base_phrase': 'market trending',
                'variations': [
                    'market trending strongly',
                    'clear directional bias',
                    'trend remains healthy',
                    'directional move intact',
                    'trend structure clear'
                ],
                'priority': 1,
                'appropriate_for': '{"structure": ["bos", "pullback"]}'
            },
            {
                'category': 'regime',
                'subcategory': 'ranging',
                'base_phrase': 'range-bound conditions',
                'variations': [
                    'range-bound conditions persist',
                    'consolidation continues',
                    'sideways price action',
                    'range established',
                    'bounded movement'
                ],
                'priority': 1,
                'appropriate_for': '{"structure": ["liquidity_sweep", "order_block"]}'
            },
            {
                'category': 'regime',
                'subcategory': 'volatile',
                'base_phrase': 'volatile conditions',
                'variations': [
                    'volatile conditions present',
                    'choppy price action',
                    'erratic movement',
                    'increased volatility',
                    'unstable conditions'
                ],
                'priority': 2,
                'appropriate_for': '{"session": ["newyork", "overlap"]}'
            },
            {
                'category': 'regime',
                'subcategory': 'consolidation',
                'base_phrase': 'consolidation phase',
                'variations': [
                    'consolidation phase active',
                    'compression detected',
                    'coiling price action',
                    'tight range forming',
                    'equilibrium reached'
                ],
                'priority': 1,
                'appropriate_for': '{"structure": ["order_block", "fvg"]}'
            },
        ]
        
        # ========== SESSION VARIATIONS ==========
        session_entries = [
            {
                'category': 'session',
                'subcategory': 'london',
                'base_phrase': 'during London session',
                'variations': [
                    'during London session',
                    'as London opens',
                    'during European hours',
                    'in London trading'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending", "volatile"]}'
            },
            {
                'category': 'session',
                'subcategory': 'newyork',
                'base_phrase': 'during New York session',
                'variations': [
                    'during New York session',
                    'as NY opens',
                    'during US hours',
                    'in New York trading'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending", "volatile"]}'
            },
            {
                'category': 'session',
                'subcategory': 'asia',
                'base_phrase': 'during Asian session',
                'variations': [
                    'during Asian session',
                    'in Asian hours',
                    'during Tokyo trading',
                    'as Asia trades'
                ],
                'priority': 2,
                'appropriate_for': '{"regime": ["ranging", "consolidation"]}'
            },
            {
                'category': 'session',
                'subcategory': 'overlap',
                'base_phrase': 'during session overlap',
                'variations': [
                    'during session overlap',
                    'as sessions converge',
                    'during high-volume overlap',
                    'with multiple markets active'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending", "volatile"]}'
            },
        ]
        
        # ========== VOLUME VARIATIONS ==========
        volume_entries = [
            {
                'category': 'volume',
                'subcategory': 'spike',
                'base_phrase': 'volume spike',
                'variations': [
                    'volume spike detected',
                    'significant volume increase',
                    'heavy volume confirmed',
                    'volume surge noted',
                    'elevated participation',
                    'strong volume support'
                ],
                'priority': 1,
                'appropriate_for': '{"structure": ["bos", "liquidity_sweep"]}'
            },
            {
                'category': 'volume',
                'subcategory': 'low',
                'base_phrase': 'low volume',
                'variations': [
                    'low volume conditions',
                    'light participation',
                    'reduced volume',
                    'minimal activity',
                    'thin volume noted'
                ],
                'priority': 2,
                'appropriate_for': '{"regime": ["ranging", "consolidation"]}'
            },
            {
                'category': 'volume',
                'subcategory': 'increasing',
                'base_phrase': 'volume increasing',
                'variations': [
                    'volume increasing gradually',
                    'participation growing',
                    'volume building',
                    'activity picking up',
                    'volume expansion'
                ],
                'priority': 1,
                'appropriate_for': '{"regime": ["trending"]}'
            },
        ]
        
        # Combine all entries
        all_entries = (
            liquidity_entries + momentum_entries + structure_entries + 
            regime_entries + session_entries + volume_entries
        )
        
        # Create entries in database
        for entry in all_entries:
            obj = VariationVocabulary.objects.create(**entry)
            created_count += 1
            self.stdout.write(
                f'  ✅ {obj.category}.{obj.subcategory}: {len(obj.variations)} variations'
            )
        
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully seeded {created_count} vocabulary entries!'))
        self.stdout.write('=' * 70 + '\n')
        
        # Summary statistics
        categories = VariationVocabulary.objects.values_list('category', flat=True).distinct()
        self.stdout.write('📊 Summary by Category:')
        for category in categories:
            count = VariationVocabulary.objects.filter(category=category).count()
            total_variations = sum(
                len(v.variations) 
                for v in VariationVocabulary.objects.filter(category=category)
            )
            self.stdout.write(f'  - {category.capitalize()}: {count} entries, {total_variations} variations')
        
        self.stdout.write('\n🎉 Vocabulary database ready for Zenith Market Analyst!')
