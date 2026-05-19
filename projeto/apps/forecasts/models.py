from django.db import models
from apps.beaches.models import Beach

# Create your models here.


class OceanCondition(models.Model):
    beach = models.ForeignKey(Beach, on_delete=models.CASCADE)

    wave_height = models.FloatField()
    tide_level = models.FloatField()

    water_temperature = models.FloatField(null=True)

    moon_phase = models.CharField(max_length=50)

    collected_at = models.DateTimeField()