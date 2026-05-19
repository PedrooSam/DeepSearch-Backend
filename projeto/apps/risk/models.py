from django.db import models
from apps.beaches.models import Beach

# Create your models here.


class RiskPrediction(models.Model):
    beach = models.ForeignKey(Beach, on_delete=models.CASCADE)

    risk_level = models.CharField(max_length=20)

    probability = models.FloatField()

    explanation = models.JSONField()

    generated_at = models.DateTimeField(auto_now_add=True)