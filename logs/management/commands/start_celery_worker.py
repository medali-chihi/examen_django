"""
Django management command to start Celery worker.
"""
from django.core.management.base import BaseCommand
import subprocess
import sys
import os

class Command(BaseCommand):
    help = 'Start Celery worker for anomaly detection tasks'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queues',
            type=str,
            default='analysis,notifications,batch_processing,celery',
            help='Comma-separated list of queues to process'
        )
        parser.add_argument(
            '--concurrency',
            type=int,
            default=4,
            help='Number of concurrent worker processes'
        )
        parser.add_argument(
            '--loglevel',
            type=str,
            default='info',
            choices=['debug', 'info', 'warning', 'error', 'critical'],
            help='Logging level'
        )

    def handle(self, *args, **options):
        queues = options['queues']
        concurrency = options['concurrency']
        loglevel = options['loglevel']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting Celery worker with queues: {queues}')
        )
        
        # Build the celery command
        cmd = [
            sys.executable, '-m', 'celery',
            '-A', 'anomaly_detection',
            'worker',
            '--queues', queues,
            '--concurrency', str(concurrency),
            '--loglevel', loglevel,
            '--without-gossip',
            '--without-mingle',
            '--without-heartbeat'
        ]
        
        try:
            # Start the worker
            subprocess.run(cmd, check=True)
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Celery worker stopped by user')
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Error starting Celery worker: {e}')
            )
