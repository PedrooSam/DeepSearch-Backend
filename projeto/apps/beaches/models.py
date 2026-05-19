from django.db import models

# Create your models here.


class Beach(models.Model):
    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=50)

    latitude = models.FloatField()
    longitude = models.FloatField()


    def __str__(self):
        return f"{self.name} - {self.city}, {self.state}"