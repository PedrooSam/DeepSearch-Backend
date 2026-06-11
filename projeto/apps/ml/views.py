import sys
import os

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

from .serializers import RiskPredictionInputSerializer, RiskPredictionOutputSerializer, ModelMetricsSerializer

# Adiciona o diretório de dados ao path para importar heuristicas.py
DADOS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "dados"
)
if DADOS_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(DADOS_DIR))

import heuristicas


@extend_schema(
    tags=["ML - Predição de Risco"],
    summary="Calcular probabilidade de ataque de tubarão",
    description=(
        "Recebe características ambientais e comportamentais do momento "
        "e retorna a probabilidade estimada de ocorrência de um ataque de tubarão, "
        "calculada por um modelo Random Forest treinado com heurísticas de domínio."
    ),
    request=RiskPredictionInputSerializer,
    responses={200: RiskPredictionOutputSerializer},
)
class PredictRiskView(APIView):
    def post(self, request):
        serializer = RiskPredictionInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        date_str = str(data["date"]) if data.get("date") else None

        result = heuristicas.predict_risk(
            activity=data["activity"],
            time_str=data.get("time"),
            date_str=date_str,
            country=data["country"],
            sea_temp=data.get("sea_temp"),
            tide_level=data.get("tide_level"),
            clima=data.get("clima"),
            air_temp=data.get("air_temp"),
            precipitation=data.get("precipitation"),
            wind_speed=data.get("wind_speed"),
            lat=data.get("lat"),
            lon=data.get("lon"),
        )

        output = RiskPredictionOutputSerializer(result)
        return Response(output.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=["ML - Métricas do Modelo"],
    summary="Obter métricas do modelo de ML",
    description="Retorna as métricas de desempenho (R² e MAE) calculadas no holdout do modelo de produção.",
    responses={200: ModelMetricsSerializer},
)
class ModelMetricsView(APIView):
    def get(self, request):
        metrics = heuristicas.get_model_metrics()
        data = {
            "r2": metrics.get("R2", 0.0),
            "mae": metrics.get("MAE", 0.0)
        }
        serializer = ModelMetricsSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)
