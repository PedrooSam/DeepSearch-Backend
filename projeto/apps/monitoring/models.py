from django.db import models
from django.conf import settings
from apps.beaches.models import Beach


class Alert(models.Model):
    SEVERITY_CHOICES = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
    ]
    ALERT_TYPE_CHOICES = [
        ('risk_increase', 'Aumento de risco'),
        ('risk_decrease', 'Redução de risco'),
    ]

    beach = models.ForeignKey(Beach, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPE_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    reason_factors = models.JSONField(default=dict)
    safety_tips = models.JSONField(default=list)
    previous_risk_level = models.CharField(max_length=20)
    current_risk_level = models.CharField(max_length=20)
    nearest_safe_beach = models.ForeignKey(
        Beach, on_delete=models.SET_NULL, null=True, blank=True, related_name='safe_redirects'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.beach.name}"


class UserBeachSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='beach_subscriptions'
    )
    beach = models.ForeignKey(Beach, on_delete=models.CASCADE, related_name='subscribers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'beach')

    def __str__(self):
        return f"{self.user} → {self.beach.name}"
