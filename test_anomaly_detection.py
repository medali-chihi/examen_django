#!/usr/bin/env python3
"""
Test script for Celery-based anomaly detection system.
Run this script to test all anomaly detection features.
"""

import requests
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime, timedelta

# Configuration
BASE_URL = "http://127.0.0.1:8000/api"
SECRET_KEY = 'django-insecure--nt99%5ilmsl+k8956-&3)w)u*55lg=vy##)s84m&2$qshvdfu'

def generate_hmac_signature(secret_key, message):
    """Generate HMAC signature for API authentication"""
    hmac_object = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(hmac_object.digest()).decode()

def test_single_log_analysis():
    """Test single log entry analysis"""
    print("\n🔍 Testing Single Log Analysis...")
    
    log_data = {
        "timestamp": datetime.now().isoformat() + "Z",
        "severity": "ERROR",
        "message": "Critical database connection failure - unable to connect after 5 retries"
    }
    
    message = json.dumps(log_data)
    signature = generate_hmac_signature(SECRET_KEY, message)
    
    headers = {
        'Content-Type': 'application/json',
        'X-HMAC-Signature': signature
    }
    
    response = requests.post(f"{BASE_URL}/logs/", data=message, headers=headers)
    
    if response.status_code == 201:
        result = response.json()
        print(f"✅ Log created successfully!")
        print(f"   Log ID: {result.get('id')}")
        print(f"   Analysis Task ID: {result.get('analysis_task_id')}")
        return result.get('analysis_task_id'), result.get('id')
    else:
        print(f"❌ Failed to create log: {response.status_code}")
        print(f"   Response: {response.text}")
        return None, None

def test_task_status(task_id):
    """Test task status monitoring"""
    print(f"\n📊 Testing Task Status for {task_id}...")
    
    for i in range(5):  # Check status 5 times
        response = requests.get(f"{BASE_URL}/task-status/{task_id}/")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Attempt {i+1}: Status = {result.get('status')}")
            
            if result.get('ready'):
                print(f"✅ Task completed!")
                if result.get('successful'):
                    print(f"   Result: {result.get('result')}")
                else:
                    print(f"   Error: {result.get('error')}")
                break
        else:
            print(f"❌ Failed to get task status: {response.status_code}")
        
        time.sleep(2)  # Wait 2 seconds between checks

def test_batch_analysis():
    """Test batch log analysis"""
    print("\n📦 Testing Batch Analysis...")
    
    log_entries = [
        {
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat() + "Z",
            "severity": "ERROR",
            "message": "Authentication failed for user admin"
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=3)).isoformat() + "Z",
            "severity": "WARNING",
            "message": "High memory usage detected: 85%"
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=1)).isoformat() + "Z",
            "severity": "ERROR",
            "message": "API timeout after 30 seconds"
        }
    ]
    
    data = {"log_entries": log_entries}
    
    response = requests.post(f"{BASE_URL}/batch-analysis/", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Batch analysis started!")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Batch size: {result.get('batch_size')}")
        return result.get('task_id')
    else:
        print(f"❌ Failed to start batch analysis: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_pattern_analysis():
    """Test pattern analysis"""
    print("\n🔍 Testing Pattern Analysis...")
    
    data = {"time_window_hours": 24}
    
    response = requests.post(f"{BASE_URL}/pattern-analysis/", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Pattern analysis started!")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Time window: {result.get('time_window_hours')} hours")
        return result.get('task_id')
    else:
        print(f"❌ Failed to start pattern analysis: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_real_time_analysis(log_ids):
    """Test real-time stream analysis"""
    print("\n⚡ Testing Real-time Stream Analysis...")
    
    if not log_ids:
        print("❌ No log IDs available for real-time analysis")
        return None
    
    data = {"log_entry_ids": log_ids}
    
    response = requests.post(f"{BASE_URL}/real-time-analysis/", json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Real-time analysis started!")
        print(f"   Task ID: {result.get('task_id')}")
        print(f"   Log entries: {result.get('log_entries_count')}")
        return result.get('task_id')
    else:
        print(f"❌ Failed to start real-time analysis: {response.status_code}")
        print(f"   Response: {response.text}")
        return None

def test_dashboard():
    """Test anomaly dashboard"""
    print("\n📊 Testing Anomaly Dashboard...")
    
    response = requests.get(f"{BASE_URL}/dashboard/")
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Dashboard data retrieved!")
        print(f"   Anomalies (24h): {result.get('anomalies_last_24h')}")
        print(f"   Anomalies (7d): {result.get('anomalies_last_7d')}")
        print(f"   Severity distribution: {result.get('severity_distribution_24h')}")
        print(f"   Recent anomalies: {len(result.get('recent_anomalies', []))}")
    else:
        print(f"❌ Failed to get dashboard data: {response.status_code}")
        print(f"   Response: {response.text}")

def create_test_logs():
    """Create multiple test logs for comprehensive testing"""
    print("\n🏗️ Creating Test Logs...")
    
    test_logs = [
        {"severity": "INFO", "message": "User login successful"},
        {"severity": "WARNING", "message": "Disk space low: 15% remaining"},
        {"severity": "ERROR", "message": "Failed to process payment transaction"},
        {"severity": "ERROR", "message": "Database query timeout after 30 seconds"},
        {"severity": "CRITICAL", "message": "System memory exhausted - emergency shutdown"},
    ]
    
    log_ids = []
    
    for i, log_data in enumerate(test_logs):
        log_data["timestamp"] = (datetime.now() - timedelta(minutes=10-i*2)).isoformat() + "Z"
        
        message = json.dumps(log_data)
        signature = generate_hmac_signature(SECRET_KEY, message)
        
        headers = {
            'Content-Type': 'application/json',
            'X-HMAC-Signature': signature
        }
        
        response = requests.post(f"{BASE_URL}/logs/", data=message, headers=headers)
        
        if response.status_code == 201:
            result = response.json()
            log_ids.append(result.get('id'))
            print(f"   ✅ Created log {i+1}: {log_data['severity']} - ID {result.get('id')}")
        else:
            print(f"   ❌ Failed to create log {i+1}: {response.status_code}")
    
    return log_ids

def main():
    """Run comprehensive anomaly detection tests"""
    print("🚀 Starting Celery Anomaly Detection Tests")
    print("=" * 50)
    
    # Test 1: Create test logs
    log_ids = create_test_logs()
    
    # Test 2: Single log analysis
    task_id, log_id = test_single_log_analysis()
    if log_id:
        log_ids.append(log_id)
    
    # Test 3: Task status monitoring
    if task_id:
        test_task_status(task_id)
    
    # Test 4: Batch analysis
    batch_task_id = test_batch_analysis()
    
    # Test 5: Pattern analysis
    pattern_task_id = test_pattern_analysis()
    
    # Test 6: Real-time analysis
    if log_ids:
        realtime_task_id = test_real_time_analysis(log_ids[:3])  # Use first 3 logs
    
    # Test 7: Dashboard
    time.sleep(5)  # Wait a bit for tasks to process
    test_dashboard()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nTask IDs for monitoring:")
    if task_id:
        print(f"   Single analysis: {task_id}")
    if batch_task_id:
        print(f"   Batch analysis: {batch_task_id}")
    if pattern_task_id:
        print(f"   Pattern analysis: {pattern_task_id}")
    
    print(f"\n📊 Check dashboard at: {BASE_URL}/dashboard/")
    print("🌸 Monitor with Flower at: http://localhost:5555 (if running)")

if __name__ == "__main__":
    main()
