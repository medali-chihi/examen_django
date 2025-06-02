from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import LogEntry, AnomalyReport


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Admin interface for LogEntry model"""

    list_display = ['id', 'timestamp', 'severity', 'colored_severity', 'truncated_message', 'has_anomaly']
    list_filter = ['severity', 'timestamp']
    search_fields = ['message', 'severity']
    readonly_fields = ['id', 'timestamp']
    ordering = ['-timestamp']
    list_per_page = 50

    fieldsets = (
        ('Log Information', {
            'fields': ('id', 'timestamp', 'severity', 'message')
        }),
    )

    def colored_severity(self, obj):
        """Display severity with color coding"""
        colors = {
            'ERROR': 'red',
            'WARNING': 'orange',
            'INFO': 'blue',
            'DEBUG': 'gray',
            'CRITICAL': 'darkred'
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.severity
        )
    colored_severity.short_description = 'Severity'

    def truncated_message(self, obj):
        """Display truncated message for list view"""
        if len(obj.message) > 100:
            return obj.message[:100] + '...'
        return obj.message
    truncated_message.short_description = 'Message'

    def has_anomaly(self, obj):
        """Check if log entry has associated anomaly reports"""
        count = obj.anomalyreport_set.count()
        if count > 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠️ {} anomal{}</span>',
                count,
                'y' if count == 1 else 'ies'
            )
        return format_html('<span style="color: green;">✓ Normal</span>')
    has_anomaly.short_description = 'Anomaly Status'


@admin.register(AnomalyReport)
class AnomalyReportAdmin(admin.ModelAdmin):
    """Admin interface for AnomalyReport model"""

    list_display = ['id', 'log_entry_link', 'anomaly_score', 'colored_score', 'truncated_summary', 'log_timestamp']
    list_filter = ['anomaly_score', 'log_entry__severity', 'log_entry__timestamp']
    search_fields = ['summary', 'log_entry__message']
    readonly_fields = ['id', 'log_entry_details']
    ordering = ['-log_entry__timestamp']
    list_per_page = 25

    fieldsets = (
        ('Anomaly Information', {
            'fields': ('id', 'log_entry', 'anomaly_score', 'summary')
        }),
        ('Related Log Entry', {
            'fields': ('log_entry_details',),
            'classes': ('collapse',)
        }),
    )

    def log_entry_link(self, obj):
        """Create a link to the related log entry"""
        url = reverse('admin:logs_logentry_change', args=[obj.log_entry.id])
        return format_html('<a href="{}">Log #{}</a>', url, obj.log_entry.id)
    log_entry_link.short_description = 'Log Entry'

    def colored_score(self, obj):
        """Display anomaly score with color coding"""
        score = obj.anomaly_score
        if score >= 0.8:
            color = 'darkred'
            icon = '🚨'
        elif score >= 0.6:
            color = 'red'
            icon = '⚠️'
        elif score >= 0.4:
            color = 'orange'
            icon = '⚡'
        else:
            color = 'green'
            icon = '✓'

        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color,
            icon,
            f"{score:.2f}"
        )
    colored_score.short_description = 'Score'

    def truncated_summary(self, obj):
        """Display truncated summary for list view"""
        if len(obj.summary) > 80:
            return obj.summary[:80] + '...'
        return obj.summary
    truncated_summary.short_description = 'Summary'

    def log_timestamp(self, obj):
        """Display the timestamp of the related log entry"""
        return obj.log_entry.timestamp
    log_timestamp.short_description = 'Log Time'
    log_timestamp.admin_order_field = 'log_entry__timestamp'

    def log_entry_details(self, obj):
        """Display detailed information about the related log entry"""
        if obj.log_entry:
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Timestamp:</strong> {}<br>'
                '<strong>Severity:</strong> <span style="color: {};">{}</span><br>'
                '<strong>Message:</strong><br>'
                '<pre style="white-space: pre-wrap; margin-top: 5px;">{}</pre>'
                '</div>',
                obj.log_entry.timestamp,
                'red' if obj.log_entry.severity in ['ERROR', 'CRITICAL'] else 'blue',
                obj.log_entry.severity,
                obj.log_entry.message
            )
        return "No log entry associated"
    log_entry_details.short_description = 'Log Entry Details'


# Customize admin site headers
admin.site.site_header = "Anomaly Detection System Admin"
admin.site.site_title = "Anomaly Detection Admin"
admin.site.index_title = "Welcome to Anomaly Detection System Administration"
