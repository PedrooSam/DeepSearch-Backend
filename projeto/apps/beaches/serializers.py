from rest_framework import serializers
from .models import Beach

class BeachSerializer(serializers.ModelSerializer):
    class Meta:
        model = Beach
        fields = '__all__'
