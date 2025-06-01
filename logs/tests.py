# logs/tests.py

from django.test import TestCase
from rest_framework.test import APIClient
from .models import LogEntry

class LogEntryTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.log_data = {
            'timestamp': '2025-06-01T12:00:00Z',
            'severity': 'ERROR',
            'message': 'Test log entry'
        }

    def test_create_log_entry(self):
        response = self.client.post('/api/logs/', self.log_data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(LogEntry.objects.count(), 1)
        self.assertEqual(LogEntry.objects.get().message, 'Test log entry')

    def test_anomaly_detection(self):
        # Simulez une détection d'anomalie ici
        pass  # À compléter avec votre logique pour tester l'analyse des journaux

    def test_invalid_hmac(self):
        response = self.client.post('/api/logs/', self.log_data, headers={'X-HMAC-Signature': 'invalid_signature'})
        self.assertEqual(response.status_code, 403)  # Forbidden