from rest_framework import viewsets
from .models import Incident
from .serializers import IncidentSerializer

# Create your views here.

@extend_schema(
    tags=["Incidentes"],  # Aqui você define uma tag para separar os endpoints por modelo
    summary="Gerenciar incidentes",
    description="Este endpoint permite criar, listar, atualizar e excluir incidentes."
)
class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer