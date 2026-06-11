from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'alerts', views.AlertViewSet, basename='alert')
router.register(r'subscriptions', views.SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('monitoring/', include(router.urls)),
    path('monitoring/nearby/', views.NearbyAlertsView.as_view(), name='nearby-alerts'),
    path('monitoring/summary/', views.AlertSummaryView.as_view(), name='alert-summary'),
]
