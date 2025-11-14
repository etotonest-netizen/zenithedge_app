# Generated manually for signals
# Migration to add MarketInsight model

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('signals', '0013_validationscore_tradevalidation'),
    ]

    operations = [
        migrations.CreateModel(
            name='MarketInsight',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(db_index=True, help_text='Market instrument (e.g., GBPJPY)', max_length=20)),
                ('timeframe', models.CharField(help_text='Analysis timeframe (e.g., 4H, 1H)', max_length=10)),
                ('regime', models.CharField(choices=[('Trend', 'Trend'), ('Breakout', 'Breakout'), ('MeanReversion', 'Mean Reversion'), ('Squeeze', 'Squeeze')], help_text='Market regime classification', max_length=20)),
                ('session', models.CharField(blank=True, choices=[('Asia', 'Asia Session'), ('London', 'London Session'), ('New York', 'New York Session')], db_index=True, help_text='FX trading session context', max_length=20, null=True)),
                ('bias', models.CharField(choices=[('bearish', 'Bearish'), ('neutral', 'Neutral'), ('bullish', 'Bullish')], default='neutral', help_text='AI-detected market bias (not trade direction)', max_length=10)),
                ('narrative', models.TextField(help_text='AI-generated market interpretation (2-3 sentences explaining context)')),
                ('market_phase', models.CharField(choices=[('accumulation', 'Accumulation'), ('expansion', 'Expansion'), ('manipulation', 'Manipulation'), ('distribution', 'Distribution')], help_text='Current market phase classification', max_length=20)),
                ('insight_index', models.FloatField(help_text="AI reasoning quality score (0-100) - replaces 'AI Score'", validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('confidence_score', models.FloatField(help_text='AI conviction in current regime analysis (not trade confidence)', validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(100.0)])),
                ('follow_up_cue', models.TextField(blank=True, help_text="Optional suggestion for what to observe (e.g., 'watch for liquidity retest near 185.30')")),
                ('strategy', models.CharField(help_text='Analysis strategy used', max_length=50)),
                ('observation_price', models.DecimalField(blank=True, decimal_places=8, help_text='Current observation price point', max_digits=20, null=True)),
                ('legacy_side', models.CharField(blank=True, help_text='DEPRECATED: Original signal direction (for migration only)', max_length=4, null=True)),
                ('legacy_sl', models.DecimalField(blank=True, decimal_places=8, help_text='DEPRECATED: Stop loss (for migration only)', max_digits=20, null=True)),
                ('legacy_tp', models.DecimalField(blank=True, decimal_places=8, help_text='DEPRECATED: Take profit (for migration only)', max_digits=20, null=True)),
                ('timestamp', models.CharField(blank=True, max_length=100, null=True)),
                ('received_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_high_quality', models.BooleanField(default=True, help_text='Whether insight passed quality threshold (insight_index >= 70)')),
                ('quality_notes', models.TextField(blank=True, help_text='Notes about insight quality or data issues')),
                ('outcome', models.CharField(choices=[('pending', 'Pending'), ('accurate', 'Accurate Analysis'), ('inaccurate', 'Inaccurate Analysis')], default='pending', help_text='Whether the market analysis proved accurate (for AI improvement)', max_length=10)),
                ('original_signal', models.OneToOneField(blank=True, help_text='Original signal this insight was derived from (migration only)', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='insight', to='signals.signal')),
                ('user', models.ForeignKey(blank=True, help_text='User who owns this insight', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='market_insights', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Market Insight',
                'verbose_name_plural': 'Market Insights',
                'ordering': ['-received_at'],
            },
        ),
        migrations.AddIndex(
            model_name='marketinsight',
            index=models.Index(fields=['-received_at', 'symbol'], name='signals_mar_receive_idx'),
        ),
        migrations.AddIndex(
            model_name='marketinsight',
            index=models.Index(fields=['strategy', 'regime'], name='signals_mar_strateg_idx'),
        ),
        migrations.AddIndex(
            model_name='marketinsight',
            index=models.Index(fields=['bias', 'market_phase'], name='signals_mar_bias_mk_idx'),
        ),
    ]
