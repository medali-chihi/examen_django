#!/usr/bin/env python3
"""
Test AI anomaly detection through REST API.
"""

import requests
import json
import time
import hmac
import hashlib
import base64
from datetime import datetime

# Configuration
BASE_URL = "http://127.0.0.1:8000/api"
SECRET_KEY = 'django-insecure--nt99%5ilmsl+k8956-&3)w)u*55lg=vy##)s84m&2$qshvdfu'

def generate_hmac_signature(secret_key, message):
    """Generate HMAC signature for API authentication"""
    hmac_object = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(hmac_object.digest()).decode()

def test_ai_anomaly_detection():
    """Test AI anomaly detection through API"""
    print("🤖 Testing AI Anomaly Detection via API")
    print("=" * 50)
    
    # Test cases designed to trigger different AI responses
    test_cases = [
        {
            "name": "Normal Login",
            "severity": "INFO",
            "message": "User authentication successful for user@example.com",
            "expected": "Normal activity"
        },
        {
            "name": "Database Error",
            "severity": "ERROR", 
            "message": "CRITICAL: Database connection pool exhausted - unable to serve requests",
            "expected": "Likely anomaly"
        },
        {
            "name": "Security Alert",
            "severity": "WARNING",
            "message": "Multiple failed login attempts detected from IP 192.168.1.100 - potential brute force attack",
            "expected": "Likely anomaly"
        },
        {
            "name": "System Performance",
            "severity": "INFO",
            "message": "System performance metrics: CPU 45%, Memory 60%, Disk 30%",
            "expected": "Normal activity"
        },
        {
            "name": "Critical System Failure",
            "severity": "CRITICAL",
            "message": "EMERGENCY: Primary server cluster down - failover initiated - data integrity at risk",
            "expected": "Definite anomaly"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Message: {test_case['message'][:60]}...")
        print(f"   Expected: {test_case['expected']}")
        
        # Prepare log data
        log_data = {
            "timestamp": datetime.now().isoformat() + "Z",
            "severity": test_case["severity"],
            "message": test_case["message"]
        }
        
        # Generate HMAC signature
        message = json.dumps(log_data)
        signature = generate_hmac_signature(SECRET_KEY, message)
        
        headers = {
            'Content-Type': 'application/json',
            'X-HMAC-Signature': signature
        }
        
        try:
            # Send request
            response = requests.post(f"{BASE_URL}/logs/", data=message, headers=headers)
            
            if response.status_code == 201:
                result = response.json()
                log_id = result.get('id')
                task_id = result.get('analysis_task_id')
                
                print(f"   ✅ Log created: ID {log_id}")
                print(f"   🔄 Analysis task: {task_id}")
                
                # Monitor task progress
                if task_id:
                    print("   ⏳ Waiting for AI analysis...")
                    
                    for attempt in range(10):  # Wait up to 20 seconds
                        time.sleep(2)
                        
                        try:
                            status_response = requests.get(f"{BASE_URL}/task-status/{task_id}/")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                
                                if status_data.get('ready'):
                                    if status_data.get('successful'):
                                        ai_result = status_data.get('result', {})
                                        anomaly_score = ai_result.get('anomaly_score')
                                        is_anomaly = ai_result.get('is_anomaly')
                                        processing_time = ai_result.get('processing_time')
                                        
                                        status_emoji = "🚨" if is_anomaly else "✅"
                                        status_text = "ANOMALY DETECTED" if is_anomaly else "NORMAL"
                                        
                                        print(f"   {status_emoji} AI Result: {status_text}")
                                        print(f"   📊 Anomaly Score: {anomaly_score}")
                                        print(f"   ⏱️  Processing Time: {processing_time:.3f}s")
                                        
                                        results.append({
                                            'test_case': test_case['name'],
                                            'anomaly_score': anomaly_score,
                                            'is_anomaly': is_anomaly,
                                            'processing_time': processing_time,
                                            'expected': test_case['expected']
                                        })
                                        break
                                    else:
                                        print(f"   ❌ Task failed: {status_data.get('error')}")
                                        break
                                else:
                                    print(f"   ⏳ Status: {status_data.get('status')}")
                        except Exception as e:
                            print(f"   ⚠️  Status check failed: {e}")
                    else:
                        print("   ⏰ Timeout waiting for AI analysis")
                
            else:
                print(f"   ❌ API request failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {e}")
    
    # Summary
    print(f"\n" + "=" * 50)
    print("📊 AI Testing Summary:")
    
    if results:
        total_tests = len(results)
        anomalies_detected = sum(1 for r in results if r['is_anomaly'])
        avg_processing_time = sum(r['processing_time'] for r in results) / total_tests
        
        print(f"   Total tests completed: {total_tests}")
        print(f"   Anomalies detected: {anomalies_detected}")
        print(f"   Normal classifications: {total_tests - anomalies_detected}")
        print(f"   Average processing time: {avg_processing_time:.3f}s")
        
        print(f"\n📋 Detailed Results:")
        for result in results:
            status = "🚨 ANOMALY" if result['is_anomaly'] else "✅ NORMAL"
            print(f"   {result['test_case']}: {status} (Score: {result['anomaly_score']})")
    else:
        print("   ❌ No tests completed successfully")
    
    return results

def test_pattern_analysis_api():
    """Test pattern analysis through API"""
    print(f"\n🔍 Testing Pattern Analysis API")
    print("=" * 50)
    
    try:
        # Trigger pattern analysis
        data = {"time_window_hours": 24}
        response = requests.post(f"{BASE_URL}/pattern-analysis/", json=data)
        
        if response.status_code == 200:
            result = response.json()
            task_id = result.get('task_id')
            
            print(f"✅ Pattern analysis started: {task_id}")
            print("⏳ Waiting for pattern analysis...")
            
            # Monitor task
            for attempt in range(15):  # Wait up to 30 seconds
                time.sleep(2)
                
                try:
                    status_response = requests.get(f"{BASE_URL}/task-status/{task_id}/")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get('ready'):
                            if status_data.get('successful'):
                                pattern_result = status_data.get('result', {})
                                
                                print(f"✅ Pattern analysis completed!")
                                print(f"   Analysis window: {pattern_result.get('analysis_window')}")
                                print(f"   Total logs analyzed: {pattern_result.get('total_logs')}")
                                print(f"   Anomaly clusters: {len(pattern_result.get('anomaly_clusters', []))}")
                                print(f"   Unusual patterns: {len(pattern_result.get('unusual_patterns', []))}")
                                
                                return pattern_result
                            else:
                                print(f"❌ Pattern analysis failed: {status_data.get('error')}")
                                return None
                        else:
                            print(f"⏳ Status: {status_data.get('status')}")
                except Exception as e:
                    print(f"⚠️  Status check failed: {e}")
            else:
                print("⏰ Timeout waiting for pattern analysis")
        else:
            print(f"❌ Pattern analysis request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Pattern analysis test failed: {e}")
    
    return None

def main():
    """Run all API AI tests"""
    print("🚀 AI Anomaly Detection API Testing")
    print("=" * 60)
    
    # Test 1: Individual anomaly detection
    anomaly_results = test_ai_anomaly_detection()
    
    # Test 2: Pattern analysis
    pattern_results = test_pattern_analysis_api()
    
    print(f"\n" + "=" * 60)
    print("🎉 AI API Testing Complete!")
    
    print(f"\n💡 Next Steps:")
    print("   1. Review AI classification accuracy")
    print("   2. Adjust BERT model if needed")
    print("   3. Fine-tune anomaly thresholds")
    print("   4. Test with real production logs")
    print("   5. Monitor performance in production")

if __name__ == "__main__":
    main()
