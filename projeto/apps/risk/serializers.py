from rest_framework import serializers


class RiskMapOutputSerializer(serializers.Serializer):
    beach_id = serializers.IntegerField()
    beach_name = serializers.CharField()
    city = serializers.CharField()
    state = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    probability = serializers.FloatField()
    risk_level = serializers.CharField()
    incident_count = serializers.IntegerField()
    factors = serializers.DictField()
