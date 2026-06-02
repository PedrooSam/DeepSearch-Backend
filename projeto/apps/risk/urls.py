from django.urls import path
from .views import RiskMapView

urlpatterns = [
    path("risk-map/", RiskMapView.as_view(), name="risk-map"),
]
