"""
Django management command to start Celery beat scheduler.
"""
from django.core.management.base import BaseCommand
import subprocess
import sys

class Command(BaseCommand):
    help = 'Start Celery beat scheduler for periodic tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            help='Logging level'
        )

    def handle(self, *args, **options):
        loglevel = options['loglevel']
        
        self.stdout.write(
            self.style.SUCCESS('Starting Celery beat scheduler')
        )
        
        # Build the celery beat command
        cmd = [
            sys.executable, '-m', 'celery',
            '-A', 'anomaly_detection',
            'beat',
            '--loglevel', loglevel,
            '--scheduler', 'django_celery_beat.schedulers:DatabaseScheduler'
        ]
        
        try:
            # Start the beat scheduler
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Celery beat scheduler stopped by user')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting Celery beat: {e}')
            )
