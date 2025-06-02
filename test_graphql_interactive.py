#!/usr/bin/env python3
"""
Script interactif pour tester l'API GraphQL du système de détection d'anomalies
Usage: python test_graphql_interactive.py
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'anomaly_detection.settings')
django.setup()

from logs.models import LogEntry, AnomalyReport


class GraphQLTester:
    """Classe pour tester l'API GraphQL"""
    
    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.graphql_url = f"{base_url}/graphql/"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def execute_query(self, query, variables=None):
        """Exécuter une requête GraphQL"""
        payload = {'query': query}
        if variables:
            payload['variables'] = variables
        
        try:
            response = self.session.post(self.graphql_url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': f'Erreur de requête: {str(e)}'}
        except json.JSONDecodeError as e:
            return {'error': f'Erreur de décodage JSON: {str(e)}'}
    
    def print_result(self, result, title="Résultat"):
        """Afficher le résultat de manière formatée"""
        print(f"\n{'='*50}")
        print(f"📊 {title}")
        print('='*50)
        
        if 'error' in result:
            print(f"❌ {result['error']}")
        elif 'errors' in result:
            print("❌ Erreurs GraphQL:")
            for error in result['errors']:
                print(f"   - {error.get('message', 'Erreur inconnue')}")
        else:
            print("✅ Succès!")
            print(json.dumps(result, indent=2, ensure_ascii=False))
    
    def test_basic_queries(self):
        """Tester les requêtes de base"""
        print("\n🚀 Test des requêtes de base...")
        
        # 1. Tous les logs
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
        result = self.execute_query(query)
        self.print_result(result, "Tous les logs")
        
        # 2. Statistiques du dashboard
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
        result = self.execute_query(query)
        self.print_result(result, "Statistiques du dashboard")
    
    def test_filtered_queries(self):
        """Tester les requêtes avec filtres"""
        print("\n🔍 Test des requêtes avec filtres...")
        
        # Logs récents
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
        variables = {'hours': 24, 'limit': 5}
        result = self.execute_query(query, variables)
        self.print_result(result, "Logs récents (24h, limite 5)")
        
        # Recherche de logs
        query = '''
        query($searchQuery: String!, $limit: Int) {
            searchLogs(query: $searchQuery, limit: $limit) {
                id
                severity
                message
            }
        }
        '''
        variables = {'searchQuery': 'error', 'limit': 3}
        result = self.execute_query(query, variables)
        self.print_result(result, "Recherche de logs (mot-clé: 'error')")
    
    def test_anomaly_queries(self):
        """Tester les requêtes d'anomalies"""
        print("\n⚠️ Test des requêtes d'anomalies...")
        
        # Toutes les anomalies
        query = '''
        query {
            allAnomalies {
                id
                anomalyScore
                summary
                logEntry {
                    id
                    timestamp
                    severity
                    message
                }
            }
        }
        '''
        result = self.execute_query(query)
        self.print_result(result, "Toutes les anomalies")
        
        # Anomalies récentes
        query = '''
        query($hours: Int, $limit: Int) {
            recentAnomalies(hours: $hours, limit: $limit) {
                id
                anomalyScore
                summary
                logEntry {
                    severity
                    message
                }
            }
        }
        '''
        variables = {'hours': 24, 'limit': 3}
        result = self.execute_query(query, variables)
        self.print_result(result, "Anomalies récentes")
    
    def test_mutations(self):
        """Tester les mutations"""
        print("\n🔧 Test des mutations...")
        
        # Créer une nouvelle entrée de log
        mutation = '''
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
        variables = {
            'severity': 'WARNING',
            'message': f'Test log créé automatiquement - {datetime.now()}'
        }
        result = self.execute_query(mutation, variables)
        self.print_result(result, "Création d'une nouvelle entrée de log")
        
        # Déclencher l'analyse de patterns
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
        result = self.execute_query(mutation, variables)
        self.print_result(result, "Déclenchement de l'analyse de patterns")
    
    def test_complex_queries(self):
        """Tester des requêtes complexes"""
        print("\n🎯 Test des requêtes complexes...")
        
        # Requête combinée pour le dashboard
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
            recentLogs(hours: 6, limit: 3) {
                id
                timestamp
                severity
                message
            }
            recentAnomalies(hours: 24, limit: 2) {
                id
                anomalyScore
                summary
                logEntry {
                    timestamp
                    severity
                }
            }
        }
        '''
        result = self.execute_query(query)
        self.print_result(result, "Requête complexe - Dashboard complet")
    
    def create_test_data(self):
        """Créer des données de test"""
        print("\n📝 Création de données de test...")
        
        try:
            # Créer quelques logs de test
            test_logs = [
                {'severity': 'ERROR', 'message': 'Erreur de connexion à la base de données'},
                {'severity': 'WARNING', 'message': 'Utilisation mémoire élevée détectée'},
                {'severity': 'INFO', 'message': 'Démarrage du service réussi'},
                {'severity': 'ERROR', 'message': 'Timeout lors de la requête API'},
                {'severity': 'DEBUG', 'message': 'Traitement du batch terminé'}
            ]
            
            from django.utils import timezone
            
            for log_data in test_logs:
                LogEntry.objects.create(
                    timestamp=timezone.now(),
                    severity=log_data['severity'],
                    message=log_data['message']
                )
            
            print(f"✅ {len(test_logs)} entrées de log créées avec succès!")
            
            # Créer une anomalie de test
            if LogEntry.objects.filter(severity='ERROR').exists():
                error_log = LogEntry.objects.filter(severity='ERROR').first()
                AnomalyReport.objects.create(
                    log_entry=error_log,
                    anomaly_score=0.75,
                    summary='Anomalie détectée: Erreurs répétées de connexion'
                )
                print("✅ Rapport d'anomalie créé avec succès!")
                
        except Exception as e:
            print(f"❌ Erreur lors de la création des données: {str(e)}")
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 Démarrage des tests GraphQL...")
        print(f"🌐 URL GraphQL: {self.graphql_url}")
        
        # Créer des données de test si nécessaire
        if LogEntry.objects.count() == 0:
            self.create_test_data()
        
        # Exécuter tous les tests
        self.test_basic_queries()
        self.test_filtered_queries()
        self.test_anomaly_queries()
        self.test_mutations()
        self.test_complex_queries()
        
        print("\n🎉 Tests terminés!")
        print(f"📊 Interface GraphiQL disponible: {self.graphql_url}")


def main():
    """Fonction principale"""
    print("🔧 Testeur GraphQL pour le Système de Détection d'Anomalies")
    print("=" * 60)
    
    tester = GraphQLTester()
    
    try:
        tester.run_all_tests()
    except KeyboardInterrupt:
        print("\n⏹️ Tests interrompus par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors des tests: {str(e)}")


if __name__ == "__main__":
    main()
