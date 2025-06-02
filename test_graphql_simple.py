#!/usr/bin/env python3
"""
Script simple pour tester GraphQL avec Python
"""

import requests
import json

# Configuration
GRAPHQL_URL = "http://127.0.0.1:8000/graphql/"

def execute_graphql(query, variables=None):
    """Exécuter une requête GraphQL"""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(GRAPHQL_URL, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {'error': str(e)}

def print_result(result, title):
    """Afficher le résultat"""
    print(f"\n{'='*50}")
    print(f"📊 {title}")
    print('='*50)
    print(json.dumps(result, indent=2, ensure_ascii=False))

# Test 1: Récupérer tous les logs
print("🚀 Test 1: Récupérer tous les logs")
query1 = '''
query {
    allLogs {
        id
        timestamp
        severity
        message
    }
}
'''
result1 = execute_graphql(query1)
print_result(result1, "Tous les logs")

# Test 2: Statistiques du dashboard
print("\n🚀 Test 2: Statistiques du dashboard")
query2 = '''
query {
    dashboardStats {
        anomaliesLast24h
        anomaliesLast7d
        totalLogs
        severityDistribution {
            severity
            count
        }
    }
}
'''
result2 = execute_graphql(query2)
print_result(result2, "Statistiques")

# Test 3: Créer un nouveau log
print("\n🚀 Test 3: Créer un nouveau log")
mutation1 = '''
mutation($severity: String!, $message: String!) {
    createLogEntry(severity: $severity, message: $message) {
        logEntry {
            id
            timestamp
            severity
            message
        }
        taskId
        success
    }
}
'''
variables1 = {
    'severity': 'WARNING',
    'message': 'Test log créé via Python script'
}
result3 = execute_graphql(mutation1, variables1)
print_result(result3, "Nouveau log créé")

# Test 4: Logs récents
print("\n🚀 Test 4: Logs récents")
query3 = '''
query($hours: Int, $limit: Int) {
    recentLogs(hours: $hours, limit: $limit) {
        id
        timestamp
        severity
        message
    }
}
'''
variables2 = {'hours': 24, 'limit': 5}
result4 = execute_graphql(query3, variables2)
print_result(result4, "Logs récents")

print("\n✅ Tests terminés!")
print(f"🌐 Interface GraphiQL: {GRAPHQL_URL}")
