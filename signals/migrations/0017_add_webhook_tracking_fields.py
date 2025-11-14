"""
Migration to add webhook tracking fields to Signal model

Adds fields for production webhook monitoring:
- raw_data: Complete JSON payload from TradingView
- source_ip: IP address of webhook request
- user_agent: User agent string from request
- status: Processing status (pending, processed, failed)
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('signals', '0016_rename_signals_mar_receive_idx_signals_mar_receive_ff78a5_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='signal',
            name='raw_data',
            field=models.JSONField(
                default=dict,
                blank=True,
                help_text='Complete raw JSON payload from webhook'
            ),
        ),
        migrations.AddField(
            model_name='signal',
            name='source_ip',
            field=models.GenericIPAddressField(
                null=True,
                blank=True,
                help_text='IP address of webhook request'
            ),
        ),
        migrations.AddField(
            model_name='signal',
            name='user_agent',
            field=models.CharField(
                max_length=500,
                blank=True,
                default='',
                help_text='User agent string from webhook request'
            ),
        ),
        migrations.AddField(
            model_name='signal',
            name='status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('pending', 'Pending Processing'),
                    ('processing', 'Processing'),
                    ('processed', 'Processed'),
                    ('failed', 'Failed'),
                ],
                default='pending',
                db_index=True,
                help_text='Webhook processing status'
            ),
        ),
        migrations.AddField(
            model_name='signal',
            name='processed_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                help_text='When signal was processed by cron job'
            ),
        ),
        migrations.AddField(
            model_name='signal',
            name='error_message',
            field=models.TextField(
                blank=True,
                default='',
                help_text='Error message if processing failed'
            ),
        ),
    ]
