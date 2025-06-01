from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from celery.result import AsyncResult
from django.utils import timezone
from .models import LogEntry, AnomalyReport
from .serializers import LogEntrySerializer
from .utils import verify_hmac
from .tasks import process_log_entry_async, send_notification_async
from rest_framework.exceptions import PermissionDenied
from django.conf import settings
import json

class LogEntryListCreate(generics.ListCreateAPIView):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer

    def create(self, request, *args, **kwargs):
        hmac_signature = request.headers.get('X-HMAC-Signature')
        message = request.body.decode()

        # Verify HMAC signature
        if hmac_signature and not verify_hmac(settings.SECRET_KEY, message, hmac_signature):
            raise PermissionDenied("Invalid HMAC signature")

        # Parse log data
        try:
            log_data = json.loads(message)
        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the log entry synchronously for immediate response
        response = super().create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            # Get the created log entry ID
            log_entry_id = response.data.get('id')
            log_message = log_data.get('message', '')

            # Start async processing for anomaly detection
            from .tasks import analyze_log_async, send_notification_async
            analysis_task = analyze_log_async.delay(log_message, log_entry_id)

            # Add task ID to response for tracking
            response.data['analysis_task_id'] = analysis_task.id
            response.data['status'] = 'processing'

        return response


@api_view(['GET'])
def task_status(request, task_id):
    """
    Get the status of a Celery task.
    """
    try:
        result = AsyncResult(task_id)

        response_data = {
            'task_id': task_id,
            'status': result.status,
            'ready': result.ready(),
            'successful': result.successful() if result.ready() else None,
            'failed': result.failed() if result.ready() else None,
        }

        if result.ready():
            if result.successful():
                response_data['result'] = result.result
            elif result.failed():
                response_data['error'] = str(result.result)

        return Response(response_data)

    except Exception as e:
        return Response(
            {'error': f'Error retrieving task status: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def trigger_batch_analysis(request):
    """
    Trigger batch analysis for multiple log entries.
    """
    try:
        log_entries = request.data.get('log_entries', [])

        if not log_entries:
            return Response(
                {'error': 'No log entries provided'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .tasks import process_log_batch
        task = process_log_batch.delay(log_entries)

        return Response({
            'message': f'Batch analysis started for {len(log_entries)} entries',
            'task_id': task.id,
            'batch_size': len(log_entries)
        })

    except Exception as e:
        return Response(
            {'error': f'Error starting batch analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def trigger_pattern_analysis(request):
    """
    Trigger advanced pattern analysis for anomaly detection.
    """
    try:
        time_window = request.data.get('time_window_hours', 24)

        if not isinstance(time_window, int) or time_window < 1:
            return Response(
                {'error': 'time_window_hours must be a positive integer'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .tasks import detect_anomaly_patterns
        task = detect_anomaly_patterns.delay(time_window)

        return Response({
            'message': f'Pattern analysis started for {time_window} hour window',
            'task_id': task.id,
            'time_window_hours': time_window
        })

    except Exception as e:
        return Response(
            {'error': f'Error starting pattern analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def real_time_stream_analysis(request):
    """
    Process a stream of log entries for real-time anomaly detection.
    """
    try:
        log_entry_ids = request.data.get('log_entry_ids', [])

        if not log_entry_ids or not isinstance(log_entry_ids, list):
            return Response(
                {'error': 'log_entry_ids must be a non-empty list'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate that all IDs are integers
        try:
            log_entry_ids = [int(id) for id in log_entry_ids]
        except (ValueError, TypeError):
            return Response(
                {'error': 'All log_entry_ids must be valid integers'},
                status=status.HTTP_400_BAD_REQUEST
            )

        from .tasks import real_time_anomaly_stream
        task = real_time_anomaly_stream.delay(log_entry_ids)

        return Response({
            'message': f'Real-time stream analysis started for {len(log_entry_ids)} entries',
            'task_id': task.id,
            'log_entries_count': len(log_entry_ids)
        })

    except Exception as e:
        return Response(
            {'error': f'Error starting real-time analysis: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def anomaly_dashboard(request):
    """
    Get dashboard data for anomaly monitoring.
    """
    try:
        # Get recent statistics
        last_24h = timezone.now() - timezone.timedelta(hours=24)
        last_7d = timezone.now() - timezone.timedelta(days=7)

        # Count anomalies
        anomalies_24h = AnomalyReport.objects.filter(
            log_entry__timestamp__gte=last_24h
        ).count()

        anomalies_7d = AnomalyReport.objects.filter(
            log_entry__timestamp__gte=last_7d
        ).count()

        # Get severity distribution for last 24h
        from django.db.models import Count
        severity_stats = LogEntry.objects.filter(
            timestamp__gte=last_24h
        ).values('severity').annotate(count=Count('severity'))

        # Get recent anomalies
        recent_anomalies = AnomalyReport.objects.select_related('log_entry').filter(
            log_entry__timestamp__gte=last_24h
        ).order_by('-log_entry__timestamp')[:10]

        recent_anomalies_data = []
        for anomaly in recent_anomalies:
            recent_anomalies_data.append({
                'id': anomaly.id,
                'timestamp': anomaly.log_entry.timestamp.isoformat(),
                'severity': anomaly.log_entry.severity,
                'message': anomaly.log_entry.message[:100] + '...' if len(anomaly.log_entry.message) > 100 else anomaly.log_entry.message,
                'anomaly_score': anomaly.anomaly_score,
                'summary': anomaly.summary
            })

        dashboard_data = {
            'anomalies_last_24h': anomalies_24h,
            'anomalies_last_7d': anomalies_7d,
            'severity_distribution_24h': {item['severity']: item['count'] for item in severity_stats},
            'recent_anomalies': recent_anomalies_data,
            'last_updated': timezone.now().isoformat()
        }

        return Response(dashboard_data)

    except Exception as e:
        return Response(
            {'error': f'Error retrieving dashboard data: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )