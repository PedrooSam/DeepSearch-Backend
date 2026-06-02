"""
Popula o banco com incidências históricas de ataques de tubarão em PE.
Uso: python3 seed_incidents.py
"""
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from apps.incidents.models import Incident
from apps.beaches.models import Beach


def get_beach(name):
    try:
        return Beach.objects.get(name=name)
    except Beach.DoesNotExist:
        return None


INCIDENTS = [
    {"beach": "Boa Viagem", "date": "2024-06-15", "incident_type": "Ataque de tubarão", "severity": "Alta", "description": "Banhista atacado na altura do posto 4, água turva após chuvas."},
    {"beach": "Boa Viagem", "date": "2023-12-02", "incident_type": "Ataque de tubarão", "severity": "Alta", "description": "Surfista mordido no braço durante maré alta no final da tarde."},
    {"beach": "Boa Viagem", "date": "2023-03-18", "incident_type": "Ataque de tubarão", "severity": "Média", "description": "Banhista sofreu mordida leve na perna. Levado ao hospital sem risco de vida."},
    {"beach": "Boa Viagem", "date": "2022-09-10", "incident_type": "Avistamento de tubarão", "severity": "Baixa", "description": "Tubarão avistado próximo à faixa de arrecifes. Praia interditada por 2h."},
    {"beach": "Piedade", "date": "2024-01-22", "incident_type": "Ataque de tubarão", "severity": "Alta", "description": "Jovem atacado enquanto surfava ao entardecer. Ferimentos graves na coxa."},
    {"beach": "Piedade", "date": "2023-07-08", "incident_type": "Ataque de tubarão", "severity": "Média", "description": "Mergulhador mordido no pé em área fora dos recifes."},
    {"beach": "Piedade", "date": "2022-11-30", "incident_type": "Avistamento de tubarão", "severity": "Baixa", "description": "Pescadores relatam presença de tubarão próximo à costa."},
    {"beach": "Candeias", "date": "2024-03-05", "incident_type": "Ataque de tubarão", "severity": "Alta", "description": "Banhista atacado em área sem proteção de recifes. Amputação de membro."},
    {"beach": "Candeias", "date": "2023-01-14", "incident_type": "Avistamento de tubarão", "severity": "Baixa", "description": "Tubarão visto por banhistas próximo à faixa de areia. Bombeiros acionados."},
    {"beach": "Pina", "date": "2023-08-20", "incident_type": "Ataque de tubarão", "severity": "Média", "description": "Pescador mordido na mão ao recolher rede. Atendido no local."},
    {"beach": "Pina", "date": "2022-05-12", "incident_type": "Avistamento de tubarão", "severity": "Baixa", "description": "Drone registra tubarão a 50m da faixa de banhistas."},
    {"beach": "Pau Amarelo", "date": "2024-02-10", "incident_type": "Avistamento de tubarão", "severity": "Baixa", "description": "Avistamento relatado por surfistas no início da manhã."},
    {"beach": "Porto de Galinhas", "date": "2023-04-25", "incident_type": "Avistamento de tubarão", "severity": "Baixa", "description": "Tubarão pequeno visto nas piscinas naturais. Sem risco aos banhistas."},
    {"beach": "Maracaípe", "date": "2023-10-03", "incident_type": "Ataque de tubarão", "severity": "Média", "description": "Surfista mordido no tornozelo durante sessão matinal."},
    {"beach": "Barra de Jangada", "date": "2024-04-18", "incident_type": "Ataque de tubarão", "severity": "Alta", "description": "Ataque grave em banhista. Região com histórico de águas profundas próximas à costa."},
]

created = 0
skipped = 0

for inc in INCIDENTS:
    beach = get_beach(inc["beach"])
    if not beach:
        print(f"  Praia '{inc['beach']}' não encontrada no banco. Pulando...")
        skipped += 1
        continue

    Incident.objects.get_or_create(
        beach=beach,
        date=inc["date"],
        incident_type=inc["incident_type"],
        defaults={
            "severity": inc["severity"],
            "description": inc["description"],
        },
    )
    created += 1

print(f"{created} incidências criadas. {skipped} puladas. Total no banco: {Incident.objects.count()}")
