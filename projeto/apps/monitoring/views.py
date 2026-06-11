from datetime import timedelta

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Alert, UserBeachSubscription
from .serializers import AlertSerializer, UserBeachSubscriptionSerializer
from .services import get_nearby_alerts


class AlertViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        qs = Alert.objects.filter(expires_at__gte=timezone.now())
        beach_id = self.request.query_params.get('beach_id')
        severity = self.request.query_params.get('severity')
        if beach_id:
            qs = qs.filter(beach_id=beach_id)
        if severity:
            qs = qs.filter(severity=severity)
        return qs.select_related('beach', 'nearest_safe_beach')


class NearbyAlertsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        radius = request.query_params.get('radius', 5)

        if not lat or not lon:
            return Response(
                {"error": "Parâmetros 'lat' e 'lon' são obrigatórios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            lat = float(lat)
            lon = float(lon)
            radius = float(radius)
        except (ValueError, TypeError):
            return Response(
                {"error": "Parâmetros devem ser numéricos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        alerts = get_nearby_alerts(lat, lon, radius)
        serializer = AlertSerializer(alerts, many=True)
        return Response(serializer.data)


@extend_schema(tags=["Monitoramento"], summary="Resumo de alertas por período")
class AlertSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        days = int(request.query_params.get('days', 7))
        start = timezone.now() - timedelta(days=days)
        alerts = Alert.objects.filter(created_at__gte=start)

        return Response({
            'total': alerts.count(),
            'high': alerts.filter(severity='high').count(),
            'medium': alerts.filter(severity='medium').count(),
            'low': alerts.filter(severity='low').count(),
            'period_days': days,
        })


class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = UserBeachSubscriptionSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserBeachSubscription.objects.none()

    def get_queryset(self):
        return UserBeachSubscription.objects.filter(
            user=self.request.user
        ).select_related('beach')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
