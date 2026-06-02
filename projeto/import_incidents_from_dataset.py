"""
Importa incidências reais de PE do dataset_tratado_final.csv para o banco.
Uso: python3 import_incidents_from_dataset.py
"""
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

import pandas as pd
from apps.incidents.models import Incident
from apps.beaches.models import Beach

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dados", "dataset_tratado_final.csv")

LOCATION_MAP = {
    "Boa Viagem": "Boa Viagem",
    "Boa Viagem, Recife": "Boa Viagem",
    "Boa Viagem Beach, Recife": "Boa Viagem",
    "Piedade": "Piedade",
    "Piedade, Recife": "Piedade",
    "Piedade Beach": "Piedade",
    "Piedade Beach, Recife": "Piedade",
    "Piedade Beach, Jaboatão dos Guararapes City, Recife": "Piedade",
    "Piedade Beach, Jaboatão dos Guararapes City": "Piedade",
    "Candeias": "Candeias",
    "Praia do Pina": "Pina",
    "Pina, Recife": "Pina",
    "Pina": "Pina",
    "Barra de Jangada": "Barra de Jangada",
    "Pau Amarelo Beach, Paulista District (17 km from Recife)": "Pau Amarelo",
    "Praia de Pau Amarelo, Recife": "Pau Amarelo",
    "Paiva": "Piedade",
}

SEVERITY_MAP = {
    "Fatal": "Alta",
    "Amputation / Severe": "Alta",
    "Bite": "Média",
    "Laceration": "Média",
    "Minor Injury": "Baixa",
    "No Injury": "Baixa",
    "Unknown": "Média",
}


def run():
    df = pd.read_csv(DATASET_PATH, encoding="latin-1")
    pe = df[df["Area"] == "Pernambuco"].copy()

    print(f"Registros de PE no dataset: {len(pe)}")

    beaches_cache = {}
    for beach in Beach.objects.all():
        beaches_cache[beach.name] = beach

    created = 0
    skipped = 0

    for _, row in pe.iterrows():
        location = str(row.get("Location", ""))
        beach_name = LOCATION_MAP.get(location)

        if not beach_name or beach_name not in beaches_cache:
            skipped += 1
            continue

        beach = beaches_cache[beach_name]

        date = row.get("Date")
        if pd.isna(date):
            skipped += 1
            continue

        injury_cat = str(row.get("Injury_category", "Unknown"))
        severity = SEVERITY_MAP.get(injury_cat, "Média")

        fatal = str(row.get("Fatal (Y/N)", ""))
        if fatal == "Y":
            severity = "Alta"

        activity = str(row.get("Activity", "Unknown"))
        injury_desc = str(row.get("Injury", ""))
        description = f"Atividade: {activity}. {injury_desc}".strip()
        if description == "Atividade: .":
            description = f"Atividade: {activity}"

        incident_type = "Ataque de tubarão"
        if "no injury" in injury_desc.lower() or "provoked" in injury_desc.lower():
            incident_type = "Incidente com tubarão"

        _, was_created = Incident.objects.get_or_create(
            beach=beach,
            date=date,
            incident_type=incident_type,
            defaults={
                "severity": severity,
                "description": description,
            },
        )
        if was_created:
            created += 1

    print(f"{created} incidências importadas. {skipped} puladas (local não mapeado).")
    print(f"Total no banco: {Incident.objects.count()}")


if __name__ == "__main__":
    run()
