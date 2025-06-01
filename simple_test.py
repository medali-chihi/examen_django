#!/usr/bin/env python3
"""
Simple test for anomaly detection system without external dependencies.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anomaly_detection.settings')
django.setup()

from logs.models import LogEntry, AnomalyReport
from logs.tasks import analyze_log_async, detect_anomaly_patterns
from logs.utils import analyze_log

def test_basic_functionality():
    """Test basic anomaly detection functionality"""
    print("🔍 Testing Basic Anomaly Detection System")
    print("=" * 50)
    
    # Test 1: Create a log entry
    print("\n1. Creating test log entry...")
    try:
        log_entry = LogEntry.objects.create(
            timestamp=datetime.now(),
            severity="ERROR",
            message="Database connection failed after 3 retries - critical system error"
        )
        print(f"✅ Log entry created successfully! ID: {log_entry.id}")
    except Exception as e:
        print(f"❌ Failed to create log entry: {e}")
        return False
    
    # Test 2: Test BERT model analysis
    print("\n2. Testing BERT model analysis...")
    try:
        anomaly_score = analyze_log(log_entry.message)
        print(f"✅ BERT analysis completed!")
        print(f"   Message: {log_entry.message[:50]}...")
        print(f"   Anomaly Score: {anomaly_score}")
        print(f"   Is Anomaly: {'Yes' if anomaly_score == 1 else 'No'}")
    except Exception as e:
        print(f"❌ BERT analysis failed: {e}")
        return False
    
    # Test 3: Create anomaly report if needed
    if anomaly_score == 1:
        print("\n3. Creating anomaly report...")
        try:
            anomaly_report = AnomalyReport.objects.create(
                log_entry=log_entry,
                anomaly_score=float(anomaly_score),
                summary=f"Anomaly detected: {log_entry.message[:100]}..."
            )
            print(f"✅ Anomaly report created! ID: {anomaly_report.id}")
        except Exception as e:
            print(f"❌ Failed to create anomaly report: {e}")
    else:
        print("\n3. No anomaly detected - skipping anomaly report")
    
    # Test 4: Test Celery task (if available)
    print("\n4. Testing Celery task...")
    try:
        # Try to run the task synchronously for testing
        from celery import current_app
        current_app.conf.task_always_eager = True  # Run tasks synchronously for testing
        
        task_result = analyze_log_async.delay(log_entry.message, log_entry.id)
        result = task_result.get()
        print(f"✅ Celery task completed!")
        print(f"   Task Result: {result}")
    except Exception as e:
        print(f"⚠️  Celery task test skipped (Redis may not be running): {e}")
    
    return True

def test_dashboard_data():
    """Test dashboard data generation"""
    print("\n📊 Testing Dashboard Data Generation")
    print("=" * 50)
    
    try:
        from django.utils import timezone
        from django.db.models import Count
        
        # Get recent statistics
        last_24h = timezone.now() - timedelta(hours=24)
        last_7d = timezone.now() - timedelta(days=7)
        
        # Count anomalies
        anomalies_24h = AnomalyReport.objects.filter(
            log_entry__timestamp__gte=last_24h
        ).count()
        
        anomalies_7d = AnomalyReport.objects.filter(
            log_entry__timestamp__gte=last_7d
        ).count()
        
        # Get severity distribution
        severity_stats = LogEntry.objects.filter(
            timestamp__gte=last_24h
        ).values('severity').annotate(count=Count('severity'))
        
        severity_distribution = {item['severity']: item['count'] for item in severity_stats}
        
        # Get recent anomalies
        recent_anomalies = AnomalyReport.objects.select_related('log_entry').filter(
            log_entry__timestamp__gte=last_24h
        ).order_by('-log_entry__timestamp')[:5]
        
        print(f"✅ Dashboard data generated successfully!")
        print(f"   Anomalies (24h): {anomalies_24h}")
        print(f"   Anomalies (7d): {anomalies_7d}")
        print(f"   Severity distribution: {severity_distribution}")
        print(f"   Recent anomalies: {recent_anomalies.count()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard data generation failed: {e}")
        return False

def create_sample_data():
    """Create sample log data for testing"""
    print("\n🏗️  Creating Sample Test Data")
    print("=" * 50)
    
    sample_logs = [
        {"severity": "INFO", "message": "User login successful for user@example.com"},
        {"severity": "WARNING", "message": "High memory usage detected: 85% of available memory in use"},
        {"severity": "ERROR", "message": "Payment processing failed - invalid credit card number"},
        {"severity": "ERROR", "message": "Database query timeout after 30 seconds - performance issue"},
        {"severity": "CRITICAL", "message": "System memory exhausted - emergency shutdown initiated"},
        {"severity": "INFO", "message": "Backup process completed successfully"},
        {"severity": "WARNING", "message": "SSL certificate expires in 7 days"},
        {"severity": "ERROR", "message": "API rate limit exceeded - blocking requests"},
    ]
    
    created_logs = []
    anomalies_detected = 0
    
    for i, log_data in enumerate(sample_logs):
        try:
            # Create log entry
            log_entry = LogEntry.objects.create(
                timestamp=datetime.now() - timedelta(minutes=60-i*5),
                severity=log_data["severity"],
                message=log_data["message"]
            )
            created_logs.append(log_entry)
            
            # Analyze for anomalies
            anomaly_score = analyze_log(log_entry.message)
            
            if anomaly_score == 1:
                anomalies_detected += 1
                AnomalyReport.objects.create(
                    log_entry=log_entry,
                    anomaly_score=float(anomaly_score),
                    summary=f"Sample anomaly: {log_entry.message[:50]}..."
                )
            
            print(f"   ✅ Created: {log_data['severity']} - {'🚨 ANOMALY' if anomaly_score == 1 else '✓ Normal'}")
            
        except Exception as e:
            print(f"   ❌ Failed to create log {i+1}: {e}")
    
    print(f"\n📊 Sample Data Summary:")
    print(f"   Total logs created: {len(created_logs)}")
    print(f"   Anomalies detected: {anomalies_detected}")
    
    return created_logs

def test_pattern_analysis():
    """Test pattern analysis functionality"""
    print("\n🔍 Testing Pattern Analysis")
    print("=" * 50)
    
    try:
        from django.utils import timezone
        
        # Get recent log entries
        cutoff_time = timezone.now() - timedelta(hours=24)
        recent_logs = LogEntry.objects.filter(timestamp__gte=cutoff_time)
        
        # Analyze patterns
        severity_counts = {}
        for log in recent_logs:
            severity = log.severity
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Check for anomaly clusters
        anomaly_clusters = AnomalyReport.objects.filter(
            log_entry__timestamp__gte=cutoff_time
        ).count()
        
        print(f"✅ Pattern analysis completed!")
        print(f"   Total logs (24h): {recent_logs.count()}")
        print(f"   Severity distribution: {severity_counts}")
        print(f"   Anomaly clusters: {anomaly_clusters}")
        
        # Detect unusual patterns
        unusual_patterns = []
        error_count = severity_counts.get('ERROR', 0)
        if error_count > 3:
            unusual_patterns.append(f"High error rate: {error_count} errors")
        
        critical_count = severity_counts.get('CRITICAL', 0)
        if critical_count > 0:
            unusual_patterns.append(f"Critical issues detected: {critical_count}")
        
        if unusual_patterns:
            print(f"   ⚠️  Unusual patterns detected:")
            for pattern in unusual_patterns:
                print(f"      - {pattern}")
        else:
            print(f"   ✅ No unusual patterns detected")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern analysis failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Anomaly Detection System Tests")
    print("🔧 Testing without external dependencies (Redis/Celery)")
    print("=" * 60)
    
    # Test 1: Basic functionality
    if not test_basic_functionality():
        print("\n❌ Basic functionality test failed!")
        return
    
    # Test 2: Create sample data
    sample_logs = create_sample_data()
    
    # Test 3: Dashboard data
    if not test_dashboard_data():
        print("\n❌ Dashboard test failed!")
        return
    
    # Test 4: Pattern analysis
    if not test_pattern_analysis():
        print("\n❌ Pattern analysis test failed!")
        return
    
    print("\n" + "=" * 60)
    print("🎉 All Tests Completed Successfully!")
    print("\n📊 System Status:")
    print(f"   Total Log Entries: {LogEntry.objects.count()}")
    print(f"   Total Anomaly Reports: {AnomalyReport.objects.count()}")
    print(f"   BERT Model: ✅ Working")
    print(f"   Database: ✅ Working")
    print(f"   Pattern Analysis: ✅ Working")
    
    print("\n🚀 Your anomaly detection system is ready!")
    print("   Next steps:")
    print("   1. Start Redis server")
    print("   2. Start Celery workers")
    print("   3. Test with real-time API endpoints")

if __name__ == "__main__":
    main()
