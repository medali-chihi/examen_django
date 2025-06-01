from django.db import models

# Create your models here.
class LogEntry(models.Model):
    timestamp = models.DateTimeField()
    severity = models.CharField(max_length=10)
    message = models.TextField()

class AnomalyReport(models.Model):
    log_entry = models.ForeignKey(LogEntry, on_delete=models.CASCADE)
    anomaly_score = models.FloatField()
    summary = models.TextField()

