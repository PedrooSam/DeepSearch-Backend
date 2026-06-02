import sys
import os
from datetime import datetime

from django.db.models import Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from apps.beaches.models import Beach
from apps.incidents.models import Incident
from .serializers import RiskMapOutputSerializer

DADOS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "dados"
)
if DADOS_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(DADOS_DIR))

import heuristicas


@extend_schema(
    tags=["Mapa de Risco"],
    summary="Retorna o risco calculado de todas as praias",
    description=(
        "Calcula o nível de risco atual para todas as praias cadastradas "
        "usando o modelo de ML, condições ambientais e histórico de incidentes. "
        "Aceita parâmetros opcionais para sobrescrever condições ambientais."
    ),
    responses={200: RiskMapOutputSerializer(many=True)},
)
class RiskMapView(APIView):
    def get(self, request):
        beaches = Beach.objects.annotate(incident_count=Count("incident"))

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%Hh%M")

        sea_temp = request.query_params.get("sea_temp")
        tide_level = request.query_params.get("tide_level")
        clima = request.query_params.get("clima")

        if sea_temp:
            sea_temp = float(sea_temp)

        max_incidents = max(
            (b.incident_count for b in beaches), default=1
        ) or 1

        results = []
        for beach in beaches:
            prediction = heuristicas.predict_risk(
                activity="Swimming",
                time_str=time_str,
                date_str=date_str,
                country="BRAZIL",
                sea_temp=sea_temp,
                tide_level=tide_level,
                clima=clima,
                lat=beach.latitude,
                lon=beach.longitude,
            )

            history_factor = beach.incident_count / max_incidents
            adjusted_probability = min(
                prediction["probability"] * (1 + 0.3 * history_factor), 1.0
            )

            if adjusted_probability >= 0.75:
                risk_level = "Alto"
            elif adjusted_probability >= 0.50:
                risk_level = "Moderado"
            elif adjusted_probability >= 0.30:
                risk_level = "Baixo"
            else:
                risk_level = "Muito baixo"

            factors = {
                "horario": heuristicas.time_risk(heuristicas.parse_hour(time_str)),
                "estacao": heuristicas.season_risk(now.month, "BRAZIL"),
                "historico_incidentes": history_factor,
            }
            if tide_level:
                factors["mare"] = heuristicas.TIDE_RISK.get(tide_level, heuristicas.DEFAULT_TIDE_RISK)
            if sea_temp:
                factors["temperatura_mar"] = heuristicas.sea_temp_risk(sea_temp)

            factors = {k: round(v, 2) for k, v in factors.items()}

            results.append({
                "beach_id": beach.id,
                "beach_name": beach.name,
                "city": beach.city,
                "state": beach.state,
                "latitude": beach.latitude,
                "longitude": beach.longitude,
                "probability": round(adjusted_probability, 4),
                "risk_level": risk_level,
                "incident_count": beach.incident_count,
                "factors": factors,
            })

        serializer = RiskMapOutputSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
