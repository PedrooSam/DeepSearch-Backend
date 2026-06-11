from django.urls import path
from .views import PredictRiskView, ModelMetricsView

urlpatterns = [
    path("ml/predict/", PredictRiskView.as_view(), name="ml-predict-risk"),
    path("ml/metrics/", ModelMetricsView.as_view(), name="ml-model-metrics"),
]
