from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IncidentViewSet

# Criando router para mapear as URLs e endpoints
router = DefaultRouter()

# Chamando o método register para linkar os endpoints às views
router.register(r'incidentes', IncidentViewSet)

# Registra as URLs do router
urlpatterns = [
    path('', include(router.urls)),
]