#!/usr/bin/env python3
"""
HMAC Signature Generator for API Testing
Usage: python generate_hmac.py
"""

import hmac
import hashlib
import base64
import json

def generate_hmac_signature(secret_key, message):
    """Generate HMAC signature for API authentication"""
    hmac_object = hmac.new(secret_key.encode(), message.encode(), hashlib.sha256)
    return base64.b64encode(hmac_object.digest()).decode()

def main():
    # Your Django secret key (from settings.py)
    SECRET_KEY = 'django-insecure--nt99%5ilmsl+k8956-&3)w)u*55lg=vy##)s84m&2$qshvdfu'
    
    # Sample log data
    log_data = {
        "timestamp": "2024-01-15T10:30:00Z",
        "severity": "ERROR", 
        "message": "Test log entry for anomaly detection"
    }
    
    # Convert to JSON string (this is what gets sent in the request body)
    message = json.dumps(log_data)
    
    # Generate HMAC signature
    signature = generate_hmac_signature(SECRET_KEY, message)
    
    print("=== HMAC Signature Generator ===")
    print(f"Message: {message}")
    print(f"HMAC Signature: {signature}")
    print("\n=== Use in Postman ===")
    print("Headers:")
    print(f"X-HMAC-Signature: {signature}")
    print(f"Content-Type: application/json")
    print(f"Authorization: Bearer YOUR_ACCESS_TOKEN")
    print("\nBody (raw JSON):")
    print(message)

if __name__ == "__main__":
    main()
