from django.urls import path
from .views import PredictRiskView

urlpatterns = [
    path("ml/predict/", PredictRiskView.as_view(), name="ml-predict-risk"),
]
