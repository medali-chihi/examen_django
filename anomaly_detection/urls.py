"""
URL configuration for anomaly_detection project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from graphene_django.views import GraphQLView
from django.views.decorators.csrf import csrf_exempt

from logs.views import LogEntryListCreate

def api_home(request):
    """API homepage with available endpoints"""
    return JsonResponse({
        "message": "🚀 Anomaly Detection System API",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/api/dashboard/",
            "logs": "/api/logs/",
            "pattern_analysis": "/api/pattern-analysis/",
            "batch_analysis": "/api/batch-analysis/",
            "real_time_analysis": "/api/real-time-analysis/",
            "task_status": "/api/task-status/{task_id}/",
            "token": "/api/token/",
            "graphql": "/graphql/",
            "graphql_playground": "/graphql/ (with GraphiQL interface)",
            "admin": "/admin/"
        },
        "status": "✅ System Ready",
        "documentation": "Check /api/dashboard/ for monitoring"
    })

urlpatterns = [
    path('', api_home, name='api-home'),
    path('admin/', admin.site.urls),
    path('api/', include('logs.urls')),
    path('logs/', LogEntryListCreate.as_view(), name='log-entry-list-create'),
    path('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True)), name='graphql'),
]
