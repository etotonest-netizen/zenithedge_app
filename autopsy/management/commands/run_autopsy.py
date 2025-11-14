"""
Management command to run autopsy analysis on insights

Usage:
    python manage.py run_autopsy --insight-id 123
    python manage.py run_autopsy --from-date 2025-11-01 --to-date 2025-11-12
    python manage.py run_autopsy --last-days 7 --horizons 4H,24H
"""
import logging
from datetime import timedelta
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db.models import Q

from signals.models import Signal
from autopsy.models import InsightAudit, AutopsyJob, JobStatusChoices
from autopsy.labeler import OutcomeLabeler, BatchLabeler
from autopsy.replay import replay_insight
from autopsy.rca import analyze_audit
from autopsy.explain import explain_insight

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Run autopsy analysis on insights'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--insight-id',
            type=int,
            help='Analyze specific insight by ID'
        )
        parser.add_argument(
            '--from-date',
            type=str,
            help='Start date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--to-date',
            type=str,
            help='End date (YYYY-MM-DD)'
        )
        parser.add_argument(
            '--last-days',
            type=int,
            help='Analyze insights from last N days'
        )
        parser.add_argument(
            '--horizons',
            type=str,
            default='4H,24H',
            help='Comma-separated evaluation horizons (e.g., 1H,4H,24H)'
        )
        parser.add_argument(
            '--symbol',
            type=str,
            help='Filter by symbol (e.g., EURUSD)'
        )
        parser.add_argument(
            '--strategy',
            type=str,
            help='Filter by strategy name'
        )
        parser.add_argument(
            '--skip-rca',
            action='store_true',
            help='Skip root cause analysis'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-analyze existing audits'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be analyzed without actually running'
        )
    
    def handle(self, *args, **options):
        try:
            # Parse horizons
            horizons = [h.strip() for h in options['horizons'].split(',')]
            
            # Build insight queryset
            insights = self._get_insights(options)
            
            if not insights.exists():
                self.stdout.write(self.style.WARNING('No insights found matching criteria'))
                return
            
            count = insights.count()
            
            if options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(f'Would analyze {count} insights with horizons: {horizons}')
                )
                self._show_sample(insights[:5])
                return
            
            self.stdout.write(f'Starting autopsy analysis for {count} insights...\n')
            
            # Create job record
            job = self._create_job(insights, horizons, options)
            
            # Run analysis
            self._run_analysis(insights, horizons, job, options)
            
            # Show summary
            self._show_summary(job)
            
        except Exception as e:
            logger.error(f"Autopsy command failed: {e}")
            raise CommandError(f'Autopsy failed: {e}')
    
    def _get_insights(self, options):
        """Build insight queryset based on filters"""
        queryset = Signal.objects.all()
        
        if options['insight_id']:
            queryset = queryset.filter(id=options['insight_id'])
        else:
            # Date filtering
            if options['last_days']:
                cutoff = timezone.now() - timedelta(days=options['last_days'])
                queryset = queryset.filter(received_at__gte=cutoff)
            elif options['from_date']:
                from datetime import datetime
                from_date = datetime.strptime(options['from_date'], '%Y-%m-%d')
                queryset = queryset.filter(received_at__gte=from_date)
                
                if options['to_date']:
                    to_date = datetime.strptime(options['to_date'], '%Y-%m-%d')
                    queryset = queryset.filter(received_at__lte=to_date)
            
            # Symbol/strategy filtering
            if options['symbol']:
                queryset = queryset.filter(symbol__iexact=options['symbol'])
            
            if options['strategy']:
                queryset = queryset.filter(strategy__icontains=options['strategy'])
        
        return queryset.order_by('-received_at')
    
    def _create_job(self, insights, horizons, options):
        """Create AutopsyJob record"""
        import uuid
        
        job = AutopsyJob.objects.create(
            job_id=f"autopsy_{uuid.uuid4().hex[:8]}",
            insight_ids=[i.id for i in insights[:1000]],  # Limit stored IDs
            horizons=horizons,
            params={
                'symbol_filter': options.get('symbol'),
                'strategy_filter': options.get('strategy'),
                'skip_rca': options.get('skip_rca', False),
                'force': options.get('force', False)
            },
            status=JobStatusChoices.RUNNING,
            total_insights=insights.count(),
            started_at=timezone.now()
        )
        
        self.stdout.write(f'Created job: {job.job_id}\n')
        return job
    
    def _run_analysis(self, insights, horizons, job, options):
        """Run full analysis pipeline"""
        completed = 0
        failed = 0
        
        for idx, insight in enumerate(insights, 1):
            try:
                self.stdout.write(f'[{idx}/{job.total_insights}] Analyzing {insight.symbol} #{insight.id}...')
                
                for horizon in horizons:
                    # Check if audit already exists
                    if not options['force']:
                        if InsightAudit.objects.filter(insight=insight, horizon=horizon).exists():
                            self.stdout.write(self.style.WARNING(f'  Audit already exists for {horizon}, skipping'))
                            continue
                    
                    # Step 1: Replay and label
                    horizon_delta = self._parse_horizon(horizon)
                    ohlcv_data = replay_insight(insight, horizon_delta)
                    
                    if not ohlcv_data:
                        self.stdout.write(self.style.WARNING(f'  No OHLCV data for {horizon}'))
                        failed += 1
                        continue
                    
                    # Step 2: Create audit with labeling
                    labeler = OutcomeLabeler(insight, horizon)
                    audit = labeler.create_audit(
                        ohlcv_data,
                        replay_verified=ohlcv_data.get('pattern_verification', {}).get('verified', False)
                    )
                    
                    self.stdout.write(self.style.SUCCESS(f'  ✓ {horizon}: {audit.outcome}'))
                    
                    # Step 3: Run RCA if failed/neutral
                    if not options['skip_rca'] and audit.outcome in ['failed', 'neutral']:
                        causes = analyze_audit(audit)
                        if causes:
                            self.stdout.write(f'    RCA: {causes[0].get_cause_display()} ({causes[0].confidence}%)')
                    
                    # Step 4: Add explanation
                    explanation = explain_insight(insight)
                    if explanation and 'error' not in explanation:
                        # Store in audit metadata
                        audit.config_snapshot['explanation'] = explanation
                        audit.save()
                
                completed += 1
                
                # Update job progress
                job.completed_audits = completed
                job.failed_audits = failed
                job.save()
                
            except Exception as e:
                logger.error(f"Error analyzing insight #{insight.id}: {e}")
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {e}'))
                failed += 1
        
        # Mark job complete
        job.status = JobStatusChoices.COMPLETED
        job.finished_at = timezone.now()
        job.completed_audits = completed
        job.failed_audits = failed
        job.save()
    
    def _parse_horizon(self, horizon: str):
        """Convert horizon string to timedelta"""
        mapping = {
            '1H': timedelta(hours=1),
            '4H': timedelta(hours=4),
            '24H': timedelta(hours=24),
            '7D': timedelta(days=7),
            '1D': timedelta(days=1),
        }
        return mapping.get(horizon, timedelta(hours=4))
    
    def _show_sample(self, insights):
        """Show sample insights that would be analyzed"""
        self.stdout.write('\nSample insights:')
        for insight in insights:
            self.stdout.write(
                f'  #{insight.id} - {insight.symbol} ({insight.timeframe}) '
                f'{insight.side} at {insight.received_at}'
            )
    
    def _show_summary(self, job):
        """Show analysis summary"""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Autopsy Complete'))
        self.stdout.write('='*60)
        self.stdout.write(f'Job ID: {job.job_id}')
        self.stdout.write(f'Total: {job.total_insights}')
        self.stdout.write(f'Completed: {job.completed_audits}')
        self.stdout.write(f'Failed: {job.failed_audits}')
        
        if job.get_duration():
            self.stdout.write(f'Duration: {job.get_duration():.1f}s')
        
        # Show outcome breakdown
        from autopsy.models import OutcomeChoices
        from django.db.models import Count
        
        outcomes = InsightAudit.objects.filter(
            insight_id__in=job.insight_ids
        ).values('outcome').annotate(count=Count('id'))
        
        self.stdout.write('\nOutcome Breakdown:')
        for outcome in outcomes:
            self.stdout.write(f"  {outcome['outcome']}: {outcome['count']}")
        
        self.stdout.write('\n✅ Check Django admin for detailed audit records')
