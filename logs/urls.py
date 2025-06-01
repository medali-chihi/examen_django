from django.urls import path
from django.http import JsonResponse
from .views import (
    LogEntryListCreate, task_status, trigger_batch_analysis,
    trigger_pattern_analysis, real_time_stream_analysis, anomaly_dashboard
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

def api_index(request):
    """API index page showing available endpoints"""
    return JsonResponse({
        "message": "🔍 Anomaly Detection API",
        "version": "1.0.0",
        "available_endpoints": {
            "logs": {
                "url": "/api/logs/",
                "methods": ["GET", "POST"],
                "description": "Create and list log entries with anomaly detection"
            },
            "dashboard": {
                "url": "/api/dashboard/",
                "methods": ["GET"],
                "description": "Anomaly monitoring dashboard with statistics"
            },
            "pattern_analysis": {
                "url": "/api/pattern-analysis/",
                "methods": ["POST"],
                "description": "Trigger advanced pattern analysis"
            },
            "batch_analysis": {
                "url": "/api/batch-analysis/",
                "methods": ["POST"],
                "description": "Process multiple log entries in batch"
            },
            "real_time_analysis": {
                "url": "/api/real-time-analysis/",
                "methods": ["POST"],
                "description": "High-speed stream processing"
            },
            "task_status": {
                "url": "/api/task-status/{task_id}/",
                "methods": ["GET"],
                "description": "Monitor Celery task progress"
            },
            "token": {
                "url": "/api/token/",
                "methods": ["POST"],
                "description": "Get JWT authentication token"
            }
        },
        "status": "✅ All systems operational",
        "quick_start": "Visit /api/dashboard/ to see current anomaly statistics"
    })

urlpatterns = [
    # API index
    path('', api_index, name='api-index'),

    # Core endpoints
    path('logs/', LogEntryListCreate.as_view(), name='log-entry-list-create'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Task monitoring
    path('task-status/<str:task_id>/', task_status, name='task-status'),

    # Anomaly detection endpoints
    path('batch-analysis/', trigger_batch_analysis, name='batch-analysis'),
    path('pattern-analysis/', trigger_pattern_analysis, name='pattern-analysis'),
    path('real-time-analysis/', real_time_stream_analysis, name='real-time-analysis'),
    path('dashboard/', anomaly_dashboard, name='anomaly-dashboard'),
]