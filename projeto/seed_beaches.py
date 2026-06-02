"""
Popula o banco com praias da região metropolitana do Recife.
Uso: python3 manage.py shell < seed_beaches.py
"""
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from apps.beaches.models import Beach

BEACHES = [
    {"name": "Boa Viagem", "city": "Recife", "state": "PE", "latitude": -8.1195, "longitude": -34.8950},
    {"name": "Pina", "city": "Recife", "state": "PE", "latitude": -8.0930, "longitude": -34.8740},
    {"name": "Piedade", "city": "Jaboatão dos Guararapes", "state": "PE", "latitude": -8.1620, "longitude": -34.9100},
    {"name": "Candeias", "city": "Jaboatão dos Guararapes", "state": "PE", "latitude": -8.1850, "longitude": -34.9180},
    {"name": "Barra de Jangada", "city": "Jaboatão dos Guararapes", "state": "PE", "latitude": -8.2100, "longitude": -34.9250},
    {"name": "Pau Amarelo", "city": "Paulista", "state": "PE", "latitude": -7.9380, "longitude": -34.8300},
    {"name": "Maria Farinha", "city": "Paulista", "state": "PE", "latitude": -7.8950, "longitude": -34.8250},
    {"name": "Porto de Galinhas", "city": "Ipojuca", "state": "PE", "latitude": -8.5060, "longitude": -35.0050},
    {"name": "Maracaípe", "city": "Ipojuca", "state": "PE", "latitude": -8.5280, "longitude": -35.0100},
    {"name": "Carne de Vaca", "city": "Goiana", "state": "PE", "latitude": -7.6090, "longitude": -34.8320},
]

created = 0
for b in BEACHES:
    _, was_created = Beach.objects.get_or_create(
        name=b["name"],
        defaults=b,
    )
    if was_created:
        created += 1

print(f"{created} praias criadas. Total no banco: {Beach.objects.count()}")
