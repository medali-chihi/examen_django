"""
Celery tasks for log processing and anomaly detection.
"""
import json
import logging
from typing import List, Dict, Any
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from .models import LogEntry, AnomalyReport
from .utils import analyze_log, verify_hmac

# Set up logging
logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_log_async(self, log_message: str, log_entry_id: int = None):
    """
    Asynchronously analyze a log message for anomalies using BERT model.
    
    Args:
        log_message (str): The log message to analyze
        log_entry_id (int): Optional ID of the LogEntry record
        
    Returns:
        dict: Analysis results including anomaly score and processing time
    """
    try:
        start_time = timezone.now()
        logger.info(f"Starting anomaly analysis for log entry {log_entry_id}")
        
        # Perform the analysis
        anomaly_score = analyze_log(log_message)
        
        end_time = timezone.now()
        processing_time = (end_time - start_time).total_seconds()
        
        result = {
            'log_entry_id': log_entry_id,
            'anomaly_score': anomaly_score,
            'processing_time': processing_time,
            'analyzed_at': end_time.isoformat(),
            'is_anomaly': anomaly_score == 1
        }
        
        # Create AnomalyReport if anomaly detected
        if anomaly_score == 1 and log_entry_id:
            try:
                log_entry = LogEntry.objects.get(id=log_entry_id)
                AnomalyReport.objects.create(
                    log_entry=log_entry,
                    anomaly_score=float(anomaly_score),
                    summary=f"Anomaly detected in log message: {log_message[:100]}..."
                )
                logger.warning(f"Anomaly detected in log entry {log_entry_id}")
            except LogEntry.DoesNotExist:
                logger.error(f"LogEntry {log_entry_id} not found")
        
        logger.info(f"Completed anomaly analysis for log entry {log_entry_id} in {processing_time:.2f}s")
        return result
        
    except Exception as exc:
        logger.error(f"Error analyzing log entry {log_entry_id}: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_notification_async(self, subject: str, message: str, recipient_list: List[str]):
    """
    Asynchronously send email notifications.
    
    Args:
        subject (str): Email subject
        message (str): Email message body
        recipient_list (List[str]): List of recipient email addresses
        
    Returns:
        dict: Notification results
    """
    try:
        logger.info(f"Sending notification to {len(recipient_list)} recipients")
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=recipient_list,
            fail_silently=False,
        )
        
        result = {
            'status': 'success',
            'recipients_count': len(recipient_list),
            'sent_at': timezone.now().isoformat()
        }
        
        logger.info(f"Successfully sent notification to {len(recipient_list)} recipients")
        return result
        
    except Exception as exc:
        logger.error(f"Error sending notification: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=30 * (self.request.retries + 1))

@shared_task(bind=True)
def process_log_entry_async(self, log_data: Dict[str, Any], hmac_signature: str = None):
    """
    Asynchronously process a complete log entry including HMAC verification,
    storage, analysis, and notifications.
    
    Args:
        log_data (dict): Log entry data
        hmac_signature (str): HMAC signature for verification
        
    Returns:
        dict: Processing results
    """
    try:
        logger.info("Starting async log entry processing")
        
        # Verify HMAC if provided
        if hmac_signature:
            message = json.dumps(log_data)
            if not verify_hmac(settings.SECRET_KEY, message, hmac_signature):
                logger.error("Invalid HMAC signature")
                return {'status': 'error', 'message': 'Invalid HMAC signature'}
        
        # Create log entry
        log_entry = LogEntry.objects.create(
            timestamp=log_data.get('timestamp', timezone.now()),
            severity=log_data.get('severity', 'INFO'),
            message=log_data.get('message', '')
        )
        
        # Start anomaly analysis task
        analysis_task = analyze_log_async.delay(
            log_message=log_entry.message,
            log_entry_id=log_entry.id
        )
        
        result = {
            'status': 'success',
            'log_entry_id': log_entry.id,
            'analysis_task_id': analysis_task.id,
            'processed_at': timezone.now().isoformat()
        }
        
        logger.info(f"Successfully processed log entry {log_entry.id}")
        return result
        
    except Exception as exc:
        logger.error(f"Error processing log entry: {str(exc)}")
        return {'status': 'error', 'message': str(exc)}

@shared_task
def process_log_batch(log_entries: List[Dict[str, Any]]):
    """
    Process multiple log entries in batch.
    
    Args:
        log_entries (List[dict]): List of log entry data
        
    Returns:
        dict: Batch processing results
    """
    try:
        logger.info(f"Starting batch processing of {len(log_entries)} log entries")
        
        results = []
        for log_data in log_entries:
            task = process_log_entry_async.delay(log_data)
            results.append({
                'log_data': log_data,
                'task_id': task.id
            })
        
        return {
            'status': 'success',
            'batch_size': len(log_entries),
            'tasks': results,
            'started_at': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"Error in batch processing: {str(exc)}")
        return {'status': 'error', 'message': str(exc)}

@shared_task(bind=True, max_retries=2)
def detect_anomaly_patterns(self, time_window_hours: int = 24):
    """
    Advanced anomaly detection: Analyze patterns across multiple log entries.

    Args:
        time_window_hours (int): Time window to analyze (default: 24 hours)

    Returns:
        dict: Pattern analysis results
    """
    try:
        logger.info(f"Starting pattern analysis for {time_window_hours} hour window")

        # Get recent log entries
        cutoff_time = timezone.now() - timezone.timedelta(hours=time_window_hours)
        recent_logs = LogEntry.objects.filter(timestamp__gte=cutoff_time)

        # Group by severity and analyze patterns
        severity_counts = {}
        anomaly_clusters = []

        for log in recent_logs:
            severity = log.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1

            # Check for anomaly clusters (multiple anomalies in short time)
            related_anomalies = AnomalyReport.objects.filter(
                log_entry__timestamp__gte=log.timestamp - timezone.timedelta(minutes=5),
                log_entry__timestamp__lte=log.timestamp + timezone.timedelta(minutes=5)
            ).count()

            if related_anomalies >= 3:  # 3+ anomalies in 10-minute window
                anomaly_clusters.append({
                    'timestamp': log.timestamp.isoformat(),
                    'cluster_size': related_anomalies,
                    'severity': severity
                })

        # Detect unusual patterns
        unusual_patterns = []

        # Check for sudden spikes in ERROR logs
        error_count = severity_counts.get('ERROR', 0)
        if error_count > 10:  # Threshold for unusual error activity
            unusual_patterns.append({
                'type': 'error_spike',
                'count': error_count,
                'description': f'Unusual spike in ERROR logs: {error_count} errors in {time_window_hours}h'
            })

        # Check for missing INFO logs (could indicate system issues)
        info_count = severity_counts.get('INFO', 0)
        if info_count < 5 and time_window_hours >= 24:  # Too few INFO logs
            unusual_patterns.append({
                'type': 'low_activity',
                'count': info_count,
                'description': f'Unusually low activity: only {info_count} INFO logs in {time_window_hours}h'
            })

        result = {
            'analysis_window': f'{time_window_hours} hours',
            'total_logs': recent_logs.count(),
            'severity_distribution': severity_counts,
            'anomaly_clusters': anomaly_clusters,
            'unusual_patterns': unusual_patterns,
            'analyzed_at': timezone.now().isoformat()
        }

        # Send alert if critical patterns detected
        if anomaly_clusters or unusual_patterns:
            alert_task = send_pattern_alert.delay(result)
            result['alert_task_id'] = alert_task.id

        logger.info(f"Pattern analysis completed: {len(unusual_patterns)} unusual patterns found")
        return result

    except Exception as exc:
        logger.error(f"Error in pattern analysis: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)  # Retry after 5 minutes

@shared_task(bind=True, max_retries=3)
def send_pattern_alert(self, analysis_result: Dict[str, Any]):
    """
    Send alert notifications for detected anomaly patterns.
    """
    try:
        clusters = analysis_result.get('anomaly_clusters', [])
        patterns = analysis_result.get('unusual_patterns', [])

        if not clusters and not patterns:
            return {'status': 'no_alerts_needed'}

        # Build alert message
        subject = "🚨 Anomaly Pattern Alert - System Monitoring"

        message_parts = [
            f"Anomaly pattern analysis completed at {analysis_result['analyzed_at']}",
            f"Analysis window: {analysis_result['analysis_window']}",
            f"Total logs analyzed: {analysis_result['total_logs']}",
            "",
            "SEVERITY DISTRIBUTION:",
        ]

        for severity, count in analysis_result['severity_distribution'].items():
            message_parts.append(f"  {severity}: {count}")

        if clusters:
            message_parts.extend([
                "",
                "🔴 ANOMALY CLUSTERS DETECTED:",
            ])
            for cluster in clusters:
                message_parts.append(
                    f"  - {cluster['cluster_size']} anomalies at {cluster['timestamp']} "
                    f"(Severity: {cluster['severity']})"
                )

        if patterns:
            message_parts.extend([
                "",
                "⚠️ UNUSUAL PATTERNS DETECTED:",
            ])
            for pattern in patterns:
                message_parts.append(f"  - {pattern['description']}")

        message_parts.extend([
            "",
            "Please investigate these patterns immediately.",
            "",
            "This is an automated alert from the Anomaly Detection System."
        ])

        message = "\n".join(message_parts)

        # Send notification
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=['chihimohamedali23@gmail.com'],  # Add more recipients as needed
            fail_silently=False,
        )

        logger.warning(f"Pattern alert sent: {len(clusters)} clusters, {len(patterns)} patterns")

        return {
            'status': 'alert_sent',
            'clusters_count': len(clusters),
            'patterns_count': len(patterns),
            'sent_at': timezone.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Error sending pattern alert: {str(exc)}")
        raise self.retry(exc=exc, countdown=60)

@shared_task(bind=True)
def real_time_anomaly_stream(self, log_entry_ids: List[int]):
    """
    Process a stream of log entries for real-time anomaly detection.
    Optimized for high-throughput scenarios.
    """
    try:
        logger.info(f"Processing real-time stream of {len(log_entry_ids)} log entries")

        # Batch process for efficiency
        log_entries = LogEntry.objects.filter(id__in=log_entry_ids)

        results = []
        anomalies_detected = 0

        for log_entry in log_entries:
            # Quick anomaly check
            start_time = timezone.now()
            anomaly_score = analyze_log(log_entry.message)
            processing_time = (timezone.now() - start_time).total_seconds()

            result = {
                'log_entry_id': log_entry.id,
                'anomaly_score': anomaly_score,
                'processing_time': processing_time,
                'is_anomaly': anomaly_score == 1
            }

            if anomaly_score == 1:
                anomalies_detected += 1

                # Create anomaly report
                AnomalyReport.objects.create(
                    log_entry=log_entry,
                    anomaly_score=float(anomaly_score),
                    summary=f"Real-time anomaly detected: {log_entry.message[:100]}..."
                )

                # Immediate notification for critical anomalies
                if log_entry.severity in ['ERROR', 'CRITICAL']:
                    send_notification_async.delay(
                        subject=f"🚨 CRITICAL Anomaly Detected - {log_entry.severity}",
                        message=f"Critical anomaly detected in real-time:\n\n"
                               f"Timestamp: {log_entry.timestamp}\n"
                               f"Severity: {log_entry.severity}\n"
                               f"Message: {log_entry.message}\n"
                               f"Anomaly Score: {anomaly_score}",
                        recipient_list=['chihimohamedali23@gmail.com']
                    )

            results.append(result)

        return {
            'status': 'completed',
            'processed_count': len(log_entry_ids),
            'anomalies_detected': anomalies_detected,
            'results': results,
            'processed_at': timezone.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Error in real-time stream processing: {str(exc)}")
        return {'status': 'error', 'message': str(exc)}

@shared_task
def cleanup_old_results():
    """
    Periodic task to clean up old anomaly reports and task results.
    """
    try:
        # Delete anomaly reports older than 30 days
        cutoff_date = timezone.now() - timezone.timedelta(days=30)
        deleted_count = AnomalyReport.objects.filter(
            log_entry__timestamp__lt=cutoff_date
        ).delete()[0]

        logger.info(f"Cleaned up {deleted_count} old anomaly reports")

        return {
            'status': 'success',
            'deleted_reports': deleted_count,
            'cleaned_at': timezone.now().isoformat()
        }

    except Exception as exc:
        logger.error(f"Error in cleanup task: {str(exc)}")
        return {'status': 'error', 'message': str(exc)}
