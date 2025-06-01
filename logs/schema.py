"""
GraphQL schema for anomaly detection system.
"""
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from celery.result import AsyncResult

from .models import LogEntry, AnomalyReport
from .tasks import (
    analyze_log_async, detect_anomaly_patterns, 
    process_log_batch, real_time_anomaly_stream
)


class LogEntryType(DjangoObjectType):
    """GraphQL type for LogEntry model"""
    class Meta:
        model = LogEntry
        fields = ('id', 'timestamp', 'severity', 'message')


class AnomalyReportType(DjangoObjectType):
    """GraphQL type for AnomalyReport model"""
    class Meta:
        model = AnomalyReport
        fields = ('id', 'log_entry', 'anomaly_score', 'summary')


class SeverityStatsType(graphene.ObjectType):
    """Type for severity statistics"""
    severity = graphene.String()
    count = graphene.Int()


class DashboardStatsType(graphene.ObjectType):
    """Type for dashboard statistics"""
    anomalies_last_24h = graphene.Int()
    anomalies_last_7d = graphene.Int()
    total_logs = graphene.Int()
    severity_distribution = graphene.List(SeverityStatsType)
    last_updated = graphene.DateTime()


class TaskStatusType(graphene.ObjectType):
    """Type for Celery task status"""
    task_id = graphene.String()
    status = graphene.String()
    ready = graphene.Boolean()
    successful = graphene.Boolean()
    failed = graphene.Boolean()
    result = graphene.JSONString()
    error = graphene.String()


class Query(graphene.ObjectType):
    """GraphQL queries for anomaly detection system"""
    
    # Basic queries
    all_logs = graphene.List(LogEntryType)
    log_by_id = graphene.Field(LogEntryType, id=graphene.Int(required=True))
    logs_by_severity = graphene.List(LogEntryType, severity=graphene.String(required=True))
    
    all_anomalies = graphene.List(AnomalyReportType)
    anomaly_by_id = graphene.Field(AnomalyReportType, id=graphene.Int(required=True))
    
    # Advanced queries
    recent_logs = graphene.List(
        LogEntryType, 
        hours=graphene.Int(default_value=24),
        limit=graphene.Int(default_value=50)
    )
    
    recent_anomalies = graphene.List(
        AnomalyReportType,
        hours=graphene.Int(default_value=24),
        limit=graphene.Int(default_value=10)
    )
    
    # Dashboard and statistics
    dashboard_stats = graphene.Field(DashboardStatsType)
    severity_distribution = graphene.List(
        SeverityStatsType,
        hours=graphene.Int(default_value=24)
    )
    
    # Task monitoring
    task_status = graphene.Field(TaskStatusType, task_id=graphene.String(required=True))
    
    # Search and filtering
    search_logs = graphene.List(
        LogEntryType,
        query=graphene.String(required=True),
        limit=graphene.Int(default_value=20)
    )

    def resolve_all_logs(self, info):
        """Get all log entries"""
        return LogEntry.objects.all().order_by('-timestamp')

    def resolve_log_by_id(self, info, id):
        """Get log entry by ID"""
        try:
            return LogEntry.objects.get(id=id)
        except LogEntry.DoesNotExist:
            return None

    def resolve_logs_by_severity(self, info, severity):
        """Get logs by severity level"""
        return LogEntry.objects.filter(severity=severity).order_by('-timestamp')

    def resolve_all_anomalies(self, info):
        """Get all anomaly reports"""
        return AnomalyReport.objects.select_related('log_entry').order_by('-log_entry__timestamp')

    def resolve_anomaly_by_id(self, info, id):
        """Get anomaly report by ID"""
        try:
            return AnomalyReport.objects.select_related('log_entry').get(id=id)
        except AnomalyReport.DoesNotExist:
            return None

    def resolve_recent_logs(self, info, hours, limit):
        """Get recent log entries"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        return LogEntry.objects.filter(
            timestamp__gte=cutoff_time
        ).order_by('-timestamp')[:limit]

    def resolve_recent_anomalies(self, info, hours, limit):
        """Get recent anomaly reports"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        return AnomalyReport.objects.select_related('log_entry').filter(
            log_entry__timestamp__gte=cutoff_time
        ).order_by('-log_entry__timestamp')[:limit]

    def resolve_dashboard_stats(self, info):
        """Get dashboard statistics"""
        last_24h = timezone.now() - timedelta(hours=24)
        last_7d = timezone.now() - timedelta(days=7)
        
        # Count anomalies
        anomalies_24h = AnomalyReport.objects.filter(
            log_entry__timestamp__gte=last_24h
        ).count()
        
        anomalies_7d = AnomalyReport.objects.filter(
            log_entry__timestamp__gte=last_7d
        ).count()
        
        total_logs = LogEntry.objects.count()
        
        # Severity distribution
        severity_stats = LogEntry.objects.filter(
            timestamp__gte=last_24h
        ).values('severity').annotate(count=Count('severity'))
        
        severity_distribution = [
            SeverityStatsType(severity=item['severity'], count=item['count'])
            for item in severity_stats
        ]
        
        return DashboardStatsType(
            anomalies_last_24h=anomalies_24h,
            anomalies_last_7d=anomalies_7d,
            total_logs=total_logs,
            severity_distribution=severity_distribution,
            last_updated=timezone.now()
        )

    def resolve_severity_distribution(self, info, hours):
        """Get severity distribution for time period"""
        cutoff_time = timezone.now() - timedelta(hours=hours)
        severity_stats = LogEntry.objects.filter(
            timestamp__gte=cutoff_time
        ).values('severity').annotate(count=Count('severity'))
        
        return [
            SeverityStatsType(severity=item['severity'], count=item['count'])
            for item in severity_stats
        ]

    def resolve_task_status(self, info, task_id):
        """Get Celery task status"""
        try:
            result = AsyncResult(task_id)
            
            task_status = TaskStatusType(
                task_id=task_id,
                status=result.status,
                ready=result.ready(),
                successful=result.successful() if result.ready() else None,
                failed=result.failed() if result.ready() else None
            )
            
            if result.ready():
                if result.successful():
                    task_status.result = result.result
                elif result.failed():
                    task_status.error = str(result.result)
            
            return task_status
            
        except Exception as e:
            return TaskStatusType(
                task_id=task_id,
                status="ERROR",
                ready=True,
                failed=True,
                error=str(e)
            )

    def resolve_search_logs(self, info, query, limit):
        """Search logs by message content"""
        return LogEntry.objects.filter(
            Q(message__icontains=query) | Q(severity__icontains=query)
        ).order_by('-timestamp')[:limit]


class CreateLogEntry(graphene.Mutation):
    """Mutation to create a new log entry with anomaly detection"""
    
    class Arguments:
        severity = graphene.String(required=True)
        message = graphene.String(required=True)
        
    log_entry = graphene.Field(LogEntryType)
    task_id = graphene.String()
    success = graphene.Boolean()
    
    def mutate(self, info, severity, message):
        """Create log entry and trigger anomaly analysis"""
        try:
            # Create log entry
            log_entry = LogEntry.objects.create(
                timestamp=timezone.now(),
                severity=severity,
                message=message
            )
            
            # Start async anomaly analysis
            task = analyze_log_async.delay(message, log_entry.id)
            
            return CreateLogEntry(
                log_entry=log_entry,
                task_id=task.id,
                success=True
            )
            
        except Exception as e:
            return CreateLogEntry(
                success=False,
                task_id=None
            )


class TriggerPatternAnalysis(graphene.Mutation):
    """Mutation to trigger pattern analysis"""
    
    class Arguments:
        time_window_hours = graphene.Int(default_value=24)
        
    task_id = graphene.String()
    success = graphene.Boolean()
    message = graphene.String()
    
    def mutate(self, info, time_window_hours):
        """Trigger pattern analysis task"""
        try:
            task = detect_anomaly_patterns.delay(time_window_hours)
            
            return TriggerPatternAnalysis(
                task_id=task.id,
                success=True,
                message=f"Pattern analysis started for {time_window_hours} hour window"
            )
            
        except Exception as e:
            return TriggerPatternAnalysis(
                success=False,
                message=f"Failed to start pattern analysis: {str(e)}"
            )


class Mutation(graphene.ObjectType):
    """GraphQL mutations for anomaly detection system"""
    
    create_log_entry = CreateLogEntry.Field()
    trigger_pattern_analysis = TriggerPatternAnalysis.Field()


# Main schema
schema = graphene.Schema(query=Query, mutation=Mutation)
