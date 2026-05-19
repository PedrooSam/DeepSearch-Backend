from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BeachViewSet

router = DefaultRouter()
router.register(r'praias', BeachViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
