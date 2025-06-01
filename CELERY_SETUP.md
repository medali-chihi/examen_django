# 🚀 Celery Setup for Anomaly Detection Project

## 📋 Overview

Celery has been successfully integrated into your Django anomaly detection project to handle:

- **Asynchronous log analysis** using BERT models
- **Background email notifications**
- **Batch processing** of multiple log entries
- **Periodic cleanup tasks**

## 🛠️ Installation & Setup

### 1. Install Redis (Message Broker)

**Windows:**
```bash
# Download and install Redis from: https://github.com/microsoftarchive/redis/releases
# Or use Docker:
docker run -d -p 6379:6379 redis:alpine
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis
```

### 2. Install Python Dependencies

```bash
pip install celery redis django-celery-beat django-celery-results
```

### 3. Run Database Migrations

```bash
python manage.py migrate
```

## 🚀 Running Celery

### Start Redis Server
```bash
# Windows (if installed locally)
redis-server

# Or using Docker
docker run -d -p 6379:6379 redis:alpine
```

### Start Celery Worker
```bash
# Option 1: Using Django management command
python manage.py start_celery_worker

# Option 2: Direct celery command
celery -A anomaly_detection worker --loglevel=info --queues=analysis,notifications,batch_processing,celery
```

### Start Celery Beat (for periodic tasks)
```bash
# Option 1: Using Django management command
python manage.py start_celery_beat

# Option 2: Direct celery command
celery -A anomaly_detection beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

## 📊 API Endpoints

### 1. Create Log Entry (Async Processing)
```http
POST /api/logs/
Content-Type: application/json
X-HMAC-Signature: your_hmac_signature

{
    "timestamp": "2024-01-15T10:30:00Z",
    "severity": "ERROR",
    "message": "Test log entry for anomaly detection"
}
```

**Response:**
```json
{
    "id": 1,
    "timestamp": "2024-01-15T10:30:00Z",
    "severity": "ERROR", 
    "message": "Test log entry for anomaly detection",
    "analysis_task_id": "abc123-def456-ghi789",
    "status": "processing"
}
```

### 2. Check Task Status
```http
GET /api/task-status/{task_id}/
```

**Response:**
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "SUCCESS",
    "ready": true,
    "successful": true,
    "failed": false,
    "result": {
        "log_entry_id": 1,
        "anomaly_score": 0,
        "processing_time": 2.34,
        "analyzed_at": "2024-01-15T10:30:05Z",
        "is_anomaly": false
    }
}
```

### 3. Batch Analysis
```http
POST /api/batch-analysis/
Content-Type: application/json

{
    "log_entries": [
        {
            "timestamp": "2024-01-15T10:30:00Z",
            "severity": "ERROR",
            "message": "First log entry"
        },
        {
            "timestamp": "2024-01-15T10:31:00Z", 
            "severity": "WARNING",
            "message": "Second log entry"
        }
    ]
}
```

## 🔧 Configuration

### Task Queues
- **analysis**: CPU-intensive BERT model analysis
- **notifications**: Email notifications
- **batch_processing**: Batch operations
- **celery**: Default queue for other tasks

### Queue-Specific Workers
```bash
# Start worker for analysis queue only (CPU-intensive)
celery -A anomaly_detection worker --queues=analysis --concurrency=2

# Start worker for notifications queue only (I/O-intensive)
celery -A anomaly_detection worker --queues=notifications --concurrency=4
```

## 📈 Monitoring

### Celery Flower (Web-based monitoring)
```bash
pip install flower
celery -A anomaly_detection flower
```
Access at: http://localhost:5555

### Task Status via API
Monitor task progress using the `/api/task-status/{task_id}/` endpoint.

## 🔄 Periodic Tasks

Add periodic tasks via Django admin or programmatically:

```python
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

# Create schedule (every 24 hours)
schedule, created = IntervalSchedule.objects.get_or_create(
    every=24,
    period=IntervalSchedule.HOURS,
)

# Create periodic task
PeriodicTask.objects.create(
    interval=schedule,
    name='Cleanup old anomaly reports',
    task='logs.tasks.cleanup_old_results',
)
```

## 🐛 Troubleshooting

### Common Issues

1. **Redis Connection Error**
   - Ensure Redis is running: `redis-cli ping`
   - Check connection: `telnet localhost 6379`

2. **Task Not Executing**
   - Verify worker is running and connected
   - Check queue names match configuration
   - Review worker logs for errors

3. **BERT Model Loading Issues**
   - Ensure sufficient memory for model loading
   - Consider using smaller models for development

### Logs
```bash
# Worker logs
celery -A anomaly_detection worker --loglevel=debug

# Beat logs  
celery -A anomaly_detection beat --loglevel=debug
```

## 🎯 Benefits Achieved

1. **Non-blocking API responses** - Log entries are created immediately
2. **Scalable processing** - Multiple workers can handle analysis tasks
3. **Fault tolerance** - Failed tasks are retried automatically
4. **Resource optimization** - CPU-intensive tasks don't block web requests
5. **Monitoring capabilities** - Track task progress and performance
6. **Batch processing** - Handle multiple log entries efficiently

## 🔜 Next Steps

1. Set up production Redis cluster
2. Configure Celery monitoring with Flower
3. Add more sophisticated task routing
4. Implement task result caching
5. Set up periodic health checks
