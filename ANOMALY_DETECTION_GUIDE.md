# 🔍 Complete Celery Anomaly Detection Integration Guide

## 🎯 Overview

Your Django project now has a comprehensive Celery-based anomaly detection system with:

- **Real-time log analysis** using BERT models
- **Pattern detection** across time windows
- **Anomaly clustering** identification
- **Automated alerting** for critical patterns
- **Dashboard monitoring** with statistics
- **Scalable processing** with multiple worker queues

## 🚀 Quick Start

### 1. Start Redis
```bash
# Option 1: Docker (Recommended)
docker run -d -p 6379:6379 --name redis-anomaly redis:alpine

# Option 2: Local installation
redis-server
```

### 2. Start Celery Workers
```bash
# Terminal 1: Analysis worker (CPU-intensive)
celery -A anomaly_detection worker --queues=analysis --concurrency=2 --loglevel=info

# Terminal 2: Real-time worker (high-throughput)
celery -A anomaly_detection worker --queues=real_time --concurrency=4 --loglevel=info

# Terminal 3: Notifications worker
celery -A anomaly_detection worker --queues=notifications --concurrency=2 --loglevel=info

# Terminal 4: General worker
celery -A anomaly_detection worker --queues=batch_processing,maintenance,celery --loglevel=info
```

### 3. Start Django Server
```bash
python manage.py runserver
```

## 📊 API Endpoints for Anomaly Detection

### 1. 🔍 Single Log Analysis
```http
POST /api/logs/
Content-Type: application/json
X-HMAC-Signature: your_hmac_signature

{
    "timestamp": "2024-01-15T10:30:00Z",
    "severity": "ERROR",
    "message": "Database connection failed after 3 retries"
}
```

**Response:**
```json
{
    "id": 1,
    "timestamp": "2024-01-15T10:30:00Z",
    "severity": "ERROR",
    "message": "Database connection failed after 3 retries",
    "analysis_task_id": "abc123-def456-ghi789",
    "status": "processing"
}
```

### 2. 📈 Pattern Analysis
```http
POST /api/pattern-analysis/
Content-Type: application/json

{
    "time_window_hours": 24
}
```

**Response:**
```json
{
    "message": "Pattern analysis started for 24 hour window",
    "task_id": "pattern-task-123",
    "time_window_hours": 24
}
```

### 3. ⚡ Real-time Stream Analysis
```http
POST /api/real-time-analysis/
Content-Type: application/json

{
    "log_entry_ids": [1, 2, 3, 4, 5]
}
```

### 4. 📊 Anomaly Dashboard
```http
GET /api/dashboard/
```

**Response:**
```json
{
    "anomalies_last_24h": 5,
    "anomalies_last_7d": 23,
    "severity_distribution_24h": {
        "ERROR": 12,
        "WARNING": 8,
        "INFO": 45
    },
    "recent_anomalies": [
        {
            "id": 1,
            "timestamp": "2024-01-15T10:30:00Z",
            "severity": "ERROR",
            "message": "Database connection failed...",
            "anomaly_score": 1.0,
            "summary": "Anomaly detected in log message..."
        }
    ],
    "last_updated": "2024-01-15T11:00:00Z"
}
```

### 5. 📋 Batch Analysis
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

### 6. 🔍 Task Status Monitoring
```http
GET /api/task-status/{task_id}/
```

## 🎛️ Advanced Features

### Anomaly Pattern Detection
The system automatically detects:

1. **Anomaly Clusters**: Multiple anomalies within 10-minute windows
2. **Error Spikes**: Unusual increases in ERROR logs
3. **Low Activity**: Suspiciously few logs (potential system issues)
4. **Severity Patterns**: Unusual distribution of log severities

### Real-time Processing
- **High-throughput**: Process multiple log entries simultaneously
- **Immediate alerts**: Critical anomalies trigger instant notifications
- **Optimized queues**: Separate workers for different task types

### Automated Alerting
- **Pattern alerts**: Email notifications for detected patterns
- **Critical anomaly alerts**: Immediate notifications for ERROR/CRITICAL anomalies
- **Customizable recipients**: Configure multiple email addresses

## 🔧 Configuration

### Worker Specialization
```bash
# CPU-intensive analysis (fewer workers, more memory)
celery -A anomaly_detection worker --queues=analysis --concurrency=2

# I/O-intensive notifications (more workers)
celery -A anomaly_detection worker --queues=notifications --concurrency=4

# Real-time processing (optimized for speed)
celery -A anomaly_detection worker --queues=real_time --concurrency=6

# Maintenance tasks (low priority)
celery -A anomaly_detection worker --queues=maintenance --concurrency=1
```

### Periodic Tasks Setup
```python
# In Django shell or management command
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json

# Pattern analysis every 6 hours
schedule_6h, _ = IntervalSchedule.objects.get_or_create(
    every=6, period=IntervalSchedule.HOURS
)

PeriodicTask.objects.create(
    interval=schedule_6h,
    name='Pattern Analysis - 6 hourly',
    task='logs.tasks.detect_anomaly_patterns',
    args=json.dumps([24])  # 24-hour window
)

# Cleanup every day
schedule_daily, _ = IntervalSchedule.objects.get_or_create(
    every=1, period=IntervalSchedule.DAYS
)

PeriodicTask.objects.create(
    interval=schedule_daily,
    name='Cleanup old results',
    task='logs.tasks.cleanup_old_results'
)
```

## 📈 Monitoring & Debugging

### Celery Flower (Web UI)
```bash
pip install flower
celery -A anomaly_detection flower
```
Access at: http://localhost:5555

### Task Monitoring
```python
# Check task status programmatically
from celery.result import AsyncResult

result = AsyncResult('your-task-id')
print(f"Status: {result.status}")
print(f"Result: {result.result}")
```

### Logs
```bash
# Worker logs with debug info
celery -A anomaly_detection worker --loglevel=debug

# Monitor specific queues
celery -A anomaly_detection events
```

## 🎯 Use Cases

### 1. Security Monitoring
- Detect unusual login patterns
- Identify potential intrusion attempts
- Monitor failed authentication spikes

### 2. System Health
- Database connection issues
- API response time anomalies
- Resource usage spikes

### 3. Application Monitoring
- Error rate increases
- Performance degradation
- Feature usage anomalies

### 4. Business Intelligence
- User behavior anomalies
- Transaction pattern changes
- Revenue impact detection

## 🔒 Security Considerations

1. **HMAC Verification**: All log entries are verified with HMAC signatures
2. **Queue Isolation**: Different task types use separate queues
3. **Error Handling**: Comprehensive retry mechanisms
4. **Data Retention**: Automatic cleanup of old data

## 🚀 Performance Tips

1. **Scale workers** based on your load:
   - Analysis: CPU-bound, fewer workers
   - Notifications: I/O-bound, more workers
   - Real-time: Speed-critical, optimized workers

2. **Monitor queue lengths** and adjust worker counts

3. **Use Redis clustering** for production environments

4. **Implement result caching** for frequently accessed data

This integration provides a production-ready, scalable anomaly detection system that can handle high-throughput log processing while maintaining real-time responsiveness!
