# logs/test_graphql.py

import json
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from .models import LogEntry, AnomalyReport


class GraphQLTestCase(TestCase):
    """Tests pour l'API GraphQL du système de détection d'anomalies"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.client = Client()
        self.graphql_url = '/graphql/'
        
        # Créer des données de test
        self.log_entry1 = LogEntry.objects.create(
            timestamp=timezone.now(),
            severity='ERROR',
            message='Test error message for GraphQL testing'
        )
        
        self.log_entry2 = LogEntry.objects.create(
            timestamp=timezone.now() - timedelta(hours=2),
            severity='INFO',
            message='Test info message for GraphQL testing'
        )
        
        self.anomaly_report = AnomalyReport.objects.create(
            log_entry=self.log_entry1,
            anomaly_score=0.85,
            summary='High anomaly score detected in test log'
        )
    
    def execute_graphql(self, query, variables=None):
        """Exécuter une requête GraphQL"""
        body = {'query': query}
        if variables:
            body['variables'] = variables
            
        response = self.client.post(
            self.graphql_url,
            json.dumps(body),
            content_type='application/json'
        )
        return response
    
    def test_all_logs_query(self):
        """Test de la requête allLogs"""
        query = '''
        query {
            allLogs {
                id
                timestamp
                severity
                message
            }
        }
        '''
        
        response = self.execute_graphql(query)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('data', data)
        self.assertIn('allLogs', data['data'])
        self.assertEqual(len(data['data']['allLogs']), 2)
    
    def test_log_by_id_query(self):
        """Test de la requête logById"""
        query = '''
        query($id: Int!) {
            logById(id: $id) {
                id
                timestamp
                severity
                message
            }
        }
        '''
        
        variables = {'id': self.log_entry1.id}
        response = self.execute_graphql(query, variables)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        log_data = data['data']['logById']
        self.assertEqual(log_data['id'], str(self.log_entry1.id))
        self.assertEqual(log_data['severity'], 'ERROR')
    
    def test_logs_by_severity_query(self):
        """Test de la requête logsBySeverity"""
        query = '''
        query($severity: String!) {
            logsBySeverity(severity: $severity) {
                id
                severity
                message
            }
        }
        '''
        
        variables = {'severity': 'ERROR'}
        response = self.execute_graphql(query, variables)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        logs = data['data']['logsBySeverity']
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['severity'], 'ERROR')
    
    def test_all_anomalies_query(self):
        """Test de la requête allAnomalies"""
        query = '''
        query {
            allAnomalies {
                id
                anomalyScore
                summary
                logEntry {
                    id
                    severity
                    message
                }
            }
        }
        '''
        
        response = self.execute_graphql(query)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        anomalies = data['data']['allAnomalies']
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(float(anomalies[0]['anomalyScore']), 0.85)
    
    def test_recent_logs_query(self):
        """Test de la requête recentLogs"""
        query = '''
        query($hours: Int, $limit: Int) {
            recentLogs(hours: $hours, limit: $limit) {
                id
                timestamp
                severity
                message
            }
        }
        '''
        
        variables = {'hours': 24, 'limit': 10}
        response = self.execute_graphql(query, variables)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        logs = data['data']['recentLogs']
        self.assertLessEqual(len(logs), 10)
    
    def test_dashboard_stats_query(self):
        """Test de la requête dashboardStats"""
        query = '''
        query {
            dashboardStats {
                anomaliesLast24h
                anomaliesLast7d
                totalLogs
                severityDistribution {
                    severity
                    count
                }
                lastUpdated
            }
        }
        '''
        
        response = self.execute_graphql(query)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        stats = data['data']['dashboardStats']
        self.assertIsInstance(stats['totalLogs'], int)
        self.assertIsInstance(stats['anomaliesLast24h'], int)
        self.assertIsInstance(stats['severityDistribution'], list)
    
    def test_search_logs_query(self):
        """Test de la requête searchLogs"""
        query = '''
        query($searchQuery: String!, $limit: Int) {
            searchLogs(query: $searchQuery, limit: $limit) {
                id
                severity
                message
            }
        }
        '''
        
        variables = {'searchQuery': 'error', 'limit': 5}
        response = self.execute_graphql(query, variables)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        logs = data['data']['searchLogs']
        self.assertIsInstance(logs, list)
    
    def test_create_log_entry_mutation(self):
        """Test de la mutation createLogEntry"""
        mutation = '''
        mutation($severity: String!, $message: String!) {
            createLogEntry(severity: $severity, message: $message) {
                logEntry {
                    id
                    severity
                    message
                    timestamp
                }
                taskId
                success
            }
        }
        '''
        
        variables = {
            'severity': 'WARNING',
            'message': 'Test mutation log entry'
        }
        
        response = self.execute_graphql(mutation, variables)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        result = data['data']['createLogEntry']
        self.assertTrue(result['success'])
        self.assertEqual(result['logEntry']['severity'], 'WARNING')
        self.assertIsNotNone(result['taskId'])
    
    def test_trigger_pattern_analysis_mutation(self):
        """Test de la mutation triggerPatternAnalysis"""
        mutation = '''
        mutation($timeWindowHours: Int) {
            triggerPatternAnalysis(timeWindowHours: $timeWindowHours) {
                taskId
                success
                message
            }
        }
        '''
        
        variables = {'timeWindowHours': 24}
        response = self.execute_graphql(mutation, variables)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        result = data['data']['triggerPatternAnalysis']
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['taskId'])
    
    def test_complex_nested_query(self):
        """Test d'une requête complexe avec plusieurs niveaux"""
        query = '''
        query {
            dashboardStats {
                anomaliesLast24h
                totalLogs
            }
            recentLogs(hours: 24, limit: 3) {
                id
                severity
                message
            }
            allAnomalies {
                id
                anomalyScore
                logEntry {
                    id
                    severity
                    timestamp
                }
            }
        }
        '''
        
        response = self.execute_graphql(query)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('dashboardStats', data['data'])
        self.assertIn('recentLogs', data['data'])
        self.assertIn('allAnomalies', data['data'])
    
    def test_error_handling(self):
        """Test de la gestion d'erreurs GraphQL"""
        # Test avec un ID inexistant
        query = '''
        query {
            logById(id: 99999) {
                id
                message
            }
        }
        '''
        
        response = self.execute_graphql(query)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIsNone(data['data']['logById'])
