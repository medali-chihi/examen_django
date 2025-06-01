#!/usr/bin/env python3
"""
Test script for AI/ML anomaly detection tasks.
"""

import os
import sys
import django
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anomaly_detection.settings')
django.setup()

from logs.models import LogEntry, AnomalyReport
from logs.utils import analyze_log
from logs.tasks import analyze_log_async

def test_bert_model_directly():
    """Test BERT model directly without Celery"""
    print("🤖 Testing BERT Model Directly")
    print("=" * 40)
    
    # Test cases with different types of messages
    test_messages = [
        {
            "message": "User login successful",
            "expected": "Normal (should be 0)",
            "type": "Normal Operation"
        },
        {
            "message": "Database connection failed after 3 retries",
            "expected": "Anomaly (might be 1)",
            "type": "Error Message"
        },
        {
            "message": "System memory exhausted - emergency shutdown",
            "expected": "Anomaly (might be 1)", 
            "type": "Critical Error"
        },
        {
            "message": "Backup completed successfully",
            "expected": "Normal (should be 0)",
            "type": "Success Message"
        },
        {
            "message": "Unauthorized access attempt detected from IP 192.168.1.100",
            "expected": "Anomaly (might be 1)",
            "type": "Security Alert"
        },
        {
            "message": "API response time: 250ms",
            "expected": "Normal (should be 0)",
            "type": "Performance Metric"
        },
        {
            "message": "CRITICAL: Payment processing service down for 15 minutes",
            "expected": "Anomaly (might be 1)",
            "type": "Service Outage"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_messages, 1):
        print(f"\n{i}. Testing: {test_case['type']}")
        print(f"   Message: {test_case['message']}")
        print(f"   Expected: {test_case['expected']}")
        
        try:
            # Analyze with BERT model
            anomaly_score = analyze_log(test_case['message'])
            
            # Interpret result
            is_anomaly = anomaly_score == 1
            status = "🚨 ANOMALY" if is_anomaly else "✅ NORMAL"
            
            print(f"   Result: {status} (Score: {anomaly_score})")
            
            results.append({
                'message': test_case['message'],
                'type': test_case['type'],
                'score': anomaly_score,
                'is_anomaly': is_anomaly
            })
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            results.append({
                'message': test_case['message'],
                'type': test_case['type'],
                'error': str(e)
            })
    
    # Summary
    print(f"\n" + "=" * 40)
    print("📊 Test Results Summary:")
    
    total_tests = len(results)
    successful_tests = len([r for r in results if 'error' not in r])
    anomalies_detected = len([r for r in results if r.get('is_anomaly', False)])
    
    print(f"   Total tests: {total_tests}")
    print(f"   Successful: {successful_tests}")
    print(f"   Anomalies detected: {anomalies_detected}")
    print(f"   Normal messages: {successful_tests - anomalies_detected}")
    
    return results

def test_celery_tasks():
    """Test Celery tasks (requires Redis and worker)"""
    print("\n🔄 Testing Celery Tasks")
    print("=" * 40)
    
    try:
        # Create a test log entry
        test_log = LogEntry.objects.create(
            timestamp=datetime.now(),
            severity="ERROR",
            message="Test error message for Celery task testing"
        )
        print(f"✅ Created test log entry: ID {test_log.id}")
        
        # Test async task
        print("🚀 Starting async anomaly analysis...")
        task = analyze_log_async.delay(test_log.message, test_log.id)
        print(f"✅ Task started: {task.id}")
        
        # Try to get result (will timeout if Redis/worker not running)
        try:
            result = task.get(timeout=10)  # Wait max 10 seconds
            print(f"✅ Task completed successfully!")
            print(f"   Result: {result}")
            
            # Check if anomaly report was created
            anomaly_reports = AnomalyReport.objects.filter(log_entry=test_log)
            if anomaly_reports.exists():
                report = anomaly_reports.first()
                print(f"✅ Anomaly report created: Score {report.anomaly_score}")
            else:
                print("ℹ️  No anomaly detected (no report created)")
                
        except Exception as e:
            print(f"⚠️  Task execution failed: {e}")
            print("   This is normal if Redis/Celery worker is not running")
        
        # Clean up
        test_log.delete()
        print("🧹 Test data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Celery task test failed: {e}")
        return False

def test_pattern_detection():
    """Test pattern detection with sample data"""
    print("\n🔍 Testing Pattern Detection")
    print("=" * 40)
    
    try:
        # Create sample log entries with patterns
        sample_logs = [
            {"severity": "INFO", "message": "User login successful"},
            {"severity": "ERROR", "message": "Database timeout error"},
            {"severity": "ERROR", "message": "Connection failed to database"},
            {"severity": "ERROR", "message": "Database query timeout"},
            {"severity": "WARNING", "message": "High memory usage detected"},
            {"severity": "CRITICAL", "message": "System overload detected"},
        ]
        
        created_logs = []
        anomaly_count = 0
        
        print("📝 Creating sample log entries...")
        for log_data in sample_logs:
            log_entry = LogEntry.objects.create(
                timestamp=datetime.now(),
                severity=log_data["severity"],
                message=log_data["message"]
            )
            created_logs.append(log_entry)
            
            # Test anomaly detection on each
            try:
                anomaly_score = analyze_log(log_entry.message)
                if anomaly_score == 1:
                    anomaly_count += 1
                    print(f"   🚨 {log_data['severity']}: ANOMALY detected")
                else:
                    print(f"   ✅ {log_data['severity']}: Normal")
            except Exception as e:
                print(f"   ⚠️  {log_data['severity']}: Analysis failed - {e}")
        
        print(f"\n📊 Pattern Detection Results:")
        print(f"   Total logs created: {len(created_logs)}")
        print(f"   Anomalies detected: {anomaly_count}")
        print(f"   Normal logs: {len(created_logs) - anomaly_count}")
        
        # Clean up
        for log in created_logs:
            log.delete()
        print("🧹 Sample data cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Pattern detection test failed: {e}")
        return False

def test_model_performance():
    """Test model performance with timing"""
    print("\n⏱️  Testing Model Performance")
    print("=" * 40)
    
    import time
    
    test_messages = [
        "Normal user activity detected",
        "CRITICAL SYSTEM FAILURE - IMMEDIATE ACTION REQUIRED",
        "Database connection established successfully",
        "Security breach detected - unauthorized access attempt",
        "Backup process completed without errors"
    ]
    
    total_time = 0
    successful_analyses = 0
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n{i}. Analyzing: {message[:50]}...")
        
        try:
            start_time = time.time()
            anomaly_score = analyze_log(message)
            end_time = time.time()
            
            analysis_time = end_time - start_time
            total_time += analysis_time
            successful_analyses += 1
            
            status = "🚨 ANOMALY" if anomaly_score == 1 else "✅ NORMAL"
            print(f"   Result: {status}")
            print(f"   Time: {analysis_time:.3f} seconds")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    if successful_analyses > 0:
        avg_time = total_time / successful_analyses
        print(f"\n📊 Performance Summary:")
        print(f"   Successful analyses: {successful_analyses}/{len(test_messages)}")
        print(f"   Total time: {total_time:.3f} seconds")
        print(f"   Average time per analysis: {avg_time:.3f} seconds")
        print(f"   Throughput: {1/avg_time:.1f} analyses per second")

def main():
    """Run all AI task tests"""
    print("🤖 AI Anomaly Detection Task Testing")
    print("=" * 50)
    
    # Test 1: BERT Model Direct Testing
    try:
        bert_results = test_bert_model_directly()
    except Exception as e:
        print(f"❌ BERT model test failed: {e}")
        print("   This might be due to missing BERT dependencies")
    
    # Test 2: Celery Tasks (optional - requires Redis)
    try:
        test_celery_tasks()
    except Exception as e:
        print(f"⚠️  Celery test skipped: {e}")
    
    # Test 3: Pattern Detection
    try:
        test_pattern_detection()
    except Exception as e:
        print(f"❌ Pattern detection test failed: {e}")
    
    # Test 4: Performance Testing
    try:
        test_model_performance()
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 AI Task Testing Complete!")
    print("\n💡 Tips:")
    print("   - If BERT tests fail, check transformers installation")
    print("   - If Celery tests fail, start Redis and Celery worker")
    print("   - Monitor performance for production optimization")
    print("   - Adjust anomaly thresholds based on your data")

if __name__ == "__main__":
    main()
