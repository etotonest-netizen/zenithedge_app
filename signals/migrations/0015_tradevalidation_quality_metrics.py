# Generated migration for adding quality_metrics to TradeValidation

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0014_add_market_insight_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='tradevalidation',
            name='quality_metrics',
            field=models.JSONField(
                default=dict,
                help_text='Narrative quality metrics: insight_index, linguistic_uniqueness, generation_time_ms'
            ),
        ),
        migrations.AddField(
            model_name='tradevalidation',
            name='kb_concepts_used',
            field=models.IntegerField(
                default=0,
                help_text='Number of Knowledge Base concepts used in narrative generation'
            ),
        ),
    ]
