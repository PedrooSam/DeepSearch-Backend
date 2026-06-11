import sys
import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db.models import Count

from apps.beaches.models import Beach
from apps.risk.models import RiskPrediction
from apps.monitoring.services import detect_risk_change, generate_alert
from apps.monitoring.marine_api import fetch_all_beaches_conditions

DADOS_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "..", "dados"
)
if DADOS_DIR not in sys.path:
    sys.path.insert(0, os.path.abspath(DADOS_DIR))

import heuristicas


def wave_height_to_tide_level(wave_height):
    if wave_height is None:
        return None
    if wave_height >= 2.0:
        return "High"
    elif wave_height >= 1.0:
        return "Medium"
    return "Low"


class Command(BaseCommand):
    help = "Busca condições marinhas reais e verifica mudanças de risco"

    def handle(self, *args, **options):
        self.stdout.write("Buscando condições marinhas via Open-Meteo...")
        marine_data = fetch_all_beaches_conditions()
        self.stdout.write(f"Dados obtidos para {len(marine_data)} praia(s).")

        beaches = Beach.objects.annotate(incident_count=Count("incident"))

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%Hh%M")

        max_incidents = max(
            (b.incident_count for b in beaches), default=1
        ) or 1

        beaches_with_risk = []
        alerts_created = 0

        for beach in beaches:
            conditions = marine_data.get(beach.id, {})

            sea_temp = conditions.get("sea_surface_temperature")
            wave_height = conditions.get("wave_height")
            tide_level = wave_height_to_tide_level(wave_height)

            prediction = heuristicas.predict_risk(
                activity="Swimming",
                time_str=time_str,
                date_str=date_str,
                country="BRAZIL",
                sea_temp=sea_temp,
                tide_level=tide_level,
                clima=None,
                lat=beach.latitude,
                lon=beach.longitude,
            )

            history_factor = beach.incident_count / max_incidents
            adjusted_probability = min(
                prediction["probability"] * (1 + 0.3 * history_factor), 1.0
            )

            if adjusted_probability >= 0.75:
                risk_level = "Alto"
            elif adjusted_probability >= 0.50:
                risk_level = "Moderado"
            elif adjusted_probability >= 0.30:
                risk_level = "Baixo"
            else:
                risk_level = "Muito baixo"

            beaches_with_risk.append((beach, risk_level))

            factors = {
                "horario": round(heuristicas.time_risk(heuristicas.parse_hour(time_str)), 2),
                "estacao": round(heuristicas.season_risk(now.month, "BRAZIL"), 2),
                "historico_incidentes": round(history_factor, 2),
            }
            if wave_height is not None:
                factors["ondas_m"] = wave_height
            if sea_temp is not None:
                factors["temperatura_mar"] = sea_temp
            if tide_level:
                factors["mare"] = tide_level

            RiskPrediction.objects.create(
                beach=beach,
                risk_level=risk_level,
                probability=adjusted_probability,
                explanation=factors,
            )

        for beach, risk_level in beaches_with_risk:
            change = detect_risk_change(beach, risk_level)
            if not change:
                continue

            conditions = marine_data.get(beach.id, {})
            factors = {
                "horario": round(heuristicas.time_risk(heuristicas.parse_hour(time_str)), 2),
                "estacao": round(heuristicas.season_risk(now.month, "BRAZIL"), 2),
            }
            if conditions.get("wave_height") is not None:
                factors["ondas_m"] = conditions["wave_height"]
            if conditions.get("sea_surface_temperature") is not None:
                factors["temperatura_mar"] = conditions["sea_surface_temperature"]

            alert = generate_alert(beach, change, factors, beaches_with_risk)
            if alert:
                alerts_created += 1
                self.stdout.write(f"  → Alerta: {alert.title}")

        self.stdout.write(
            self.style.SUCCESS(f"Verificação concluída. {alerts_created} alerta(s) criado(s).")
        )
