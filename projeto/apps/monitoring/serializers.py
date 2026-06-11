from rest_framework import serializers
from .models import Alert, UserBeachSubscription


class AlertSerializer(serializers.ModelSerializer):
    beach_name = serializers.CharField(source='beach.name', read_only=True)
    nearest_safe_beach_name = serializers.CharField(
        source='nearest_safe_beach.name', read_only=True, default=None
    )
    nearest_safe_beach_lat = serializers.FloatField(
        source='nearest_safe_beach.latitude', read_only=True, default=None
    )
    nearest_safe_beach_lon = serializers.FloatField(
        source='nearest_safe_beach.longitude', read_only=True, default=None
    )

    class Meta:
        model = Alert
        fields = [
            'id', 'beach', 'beach_name', 'alert_type', 'severity',
            'title', 'message', 'reason_factors', 'safety_tips',
            'previous_risk_level', 'current_risk_level',
            'nearest_safe_beach', 'nearest_safe_beach_name',
            'nearest_safe_beach_lat', 'nearest_safe_beach_lon',
            'created_at', 'expires_at',
        ]


class UserBeachSubscriptionSerializer(serializers.ModelSerializer):
    beach_name = serializers.CharField(source='beach.name', read_only=True)

    class Meta:
        model = UserBeachSubscription
        fields = ['id', 'beach', 'beach_name', 'created_at']

    def validate_beach(self, value):
        user = self.context['request'].user
        if UserBeachSubscription.objects.filter(user=user, beach=value).exists():
            raise serializers.ValidationError("Você já está inscrito nesta praia.")
        return value
