# logs/test_graphql_django.py

import json
from django.test import TestCase, Client
from django.utils import timezone
from datetime import timedelta
from .models import LogEntry, AnomalyReport


class GraphQLTestCase(TestCase):
    """Tests GraphQL pour le système de détection d'anomalies"""
    
    def setUp(self):
        """Configuration des tests"""
        self.client = Client()
        self.graphql_url = '/graphql/'
        
        # Créer des données de test
        self.log1 = LogEntry.objects.create(
            timestamp=timezone.now(),
            severity='ERROR',
            message='Erreur de connexion base de données'
        )
        
        self.log2 = LogEntry.objects.create(
            timestamp=timezone.now() - timedelta(hours=1),
            severity='INFO',
            message='Service démarré avec succès'
        )
        
        self.anomaly = AnomalyReport.objects.create(
            log_entry=self.log1,
            anomaly_score=0.85,
            summary='Anomalie détectée: erreur répétée'
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
        """Test: récupérer tous les logs"""
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
        self.assertEqual(len(data['data']['allLogs']), 2)
        
        print("✅ Test allLogs réussi")
    
    def test_log_by_id_query(self):
        """Test: récupérer un log par ID"""
        query = '''
        query($id: Int!) {
            logById(id: $id) {
                id
                severity
                message
            }
        }
        '''
        
        variables = {'id': self.log1.id}
        response = self.execute_graphql(query, variables)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        log_data = data['data']['logById']
        self.assertEqual(log_data['severity'], 'ERROR')
        
        print("✅ Test logById réussi")
    
    def test_dashboard_stats_query(self):
        """Test: statistiques du dashboard"""
        query = '''
        query {
            dashboardStats {
                anomaliesLast24h
                totalLogs
                severityDistribution {
                    severity
                    count
                }
            }
        }
        '''
        
        response = self.execute_graphql(query)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        stats = data['data']['dashboardStats']
        self.assertEqual(stats['totalLogs'], 2)
        self.assertEqual(stats['anomaliesLast24h'], 1)
        
        print("✅ Test dashboardStats réussi")
    
    def test_create_log_mutation(self):
        """Test: créer un nouveau log"""
        mutation = '''
        mutation($severity: String!, $message: String!) {
            createLogEntry(severity: $severity, message: $message) {
                logEntry {
                    id
                    severity
                    message
                }
                success
                taskId
            }
        }
        '''
        
        variables = {
            'severity': 'WARNING',
            'message': 'Test mutation Django'
        }
        
        response = self.execute_graphql(mutation, variables)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        result = data['data']['createLogEntry']
        self.assertTrue(result['success'])
        self.assertEqual(result['logEntry']['severity'], 'WARNING')
        
        # Vérifier que le log a été créé en base
        self.assertEqual(LogEntry.objects.count(), 3)
        
        print("✅ Test createLogEntry réussi")
    
    def test_all_anomalies_query(self):
        """Test: récupérer toutes les anomalies"""
        query = '''
        query {
            allAnomalies {
                id
                anomalyScore
                summary
                logEntry {
                    id
                    severity
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
        
        print("✅ Test allAnomalies réussi")
    
    def test_recent_logs_query(self):
        """Test: logs récents avec paramètres"""
        query = '''
        query($hours: Int, $limit: Int) {
            recentLogs(hours: $hours, limit: $limit) {
                id
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
        
        print("✅ Test recentLogs réussi")
    
    def test_complex_query(self):
        """Test: requête complexe combinée"""
        query = '''
        query {
            dashboardStats {
                totalLogs
                anomaliesLast24h
            }
            recentLogs(hours: 24, limit: 2) {
                id
                severity
            }
            allAnomalies {
                id
                anomalyScore
            }
        }
        '''
        
        response = self.execute_graphql(query)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('dashboardStats', data['data'])
        self.assertIn('recentLogs', data['data'])
        self.assertIn('allAnomalies', data['data'])
        
        print("✅ Test requête complexe réussi")
    
    def test_error_handling(self):
        """Test: gestion d'erreurs"""
        # Test avec ID inexistant
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
        
        print("✅ Test gestion d'erreurs réussi")
