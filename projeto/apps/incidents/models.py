from django.db import models
from apps.beaches.models import Beach

# Create your models here.


class Incident(models.Model):
    beach = models.ForeignKey(Beach, on_delete=models.CASCADE)

    date = models.DateField()

    incident_type = models.CharField(max_length=100)

    severity = models.CharField(max_length=50)

    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.incident_type} - {self.date}"