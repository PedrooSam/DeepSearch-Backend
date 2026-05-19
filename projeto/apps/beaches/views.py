from rest_framework import viewsets
from drf_spectacular.utils import extend_schema
from .models import Beach
from .serializers import BeachSerializer

@extend_schema(tags=['Beaches'])
class BeachViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Beach.objects.all()
    serializer_class = BeachSerializer
