from rest_framework import serializers
from .models import LogEntry, AnomalyReport

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = ['id', 'timestamp', 'severity', 'message']


class AnomalyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnomalyReport
        fields = '__all__'