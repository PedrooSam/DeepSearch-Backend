from django.contrib import admin
from .models import Alert, UserBeachSubscription


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'beach', 'severity', 'alert_type', 'created_at', 'expires_at')
    list_filter = ('severity', 'alert_type')
    search_fields = ('beach__name', 'title')


@admin.register(UserBeachSubscription)
class UserBeachSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'beach', 'created_at')
    list_filter = ('beach',)
