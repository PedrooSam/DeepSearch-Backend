from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.beaches.models import Beach
from apps.monitoring.models import Alert
from apps.monitoring.services import find_nearest_safe_beach, SAFETY_TIPS


SCENARIOS = [
    {
        'alert_type': 'risk_increase',
        'previous_risk_level': 'Baixo',
        'current_risk_level': 'Alto',
        'severity': 'high',
        'reason_factors': {
            'mare': 'Alta',
            'ondas': '2.5m',
            'horario': 0.85,
        },
    },
    {
        'alert_type': 'risk_increase',
        'previous_risk_level': 'Muito baixo',
        'current_risk_level': 'Moderado',
        'severity': 'medium',
        'reason_factors': {
            'mare': 'Média',
            'temperatura_mar': 0.7,
            'horario': 0.6,
        },
    },
    {
        'alert_type': 'risk_decrease',
        'previous_risk_level': 'Alto',
        'current_risk_level': 'Baixo',
        'severity': 'low',
        'reason_factors': {
            'mare': 'Baixa',
            'horario': 0.3,
        },
    },
]


class Command(BaseCommand):
    help = "Cria alertas de exemplo para testar a funcionalidade de monitoramento"

    def handle(self, *args, **options):
        beaches = list(Beach.objects.all())

        if not beaches:
            self.stdout.write(self.style.ERROR(
                "Nenhuma praia cadastrada. Rode seed_beaches primeiro."
            ))
            return

        Alert.objects.all().delete()
        self.stdout.write("Alertas anteriores removidos.")

        now = timezone.now()
        beaches_with_safe_risk = [(b, 'Baixo') for b in beaches]
        created = 0

        for i, beach in enumerate(beaches):
            scenario = SCENARIOS[i % len(SCENARIOS)]
            current_level = scenario['current_risk_level']

            nearest_safe = None
            if current_level in ('Alto', 'Moderado'):
                nearest_safe = find_nearest_safe_beach(beach, beaches_with_safe_risk)

            Alert.objects.create(
                beach=beach,
                alert_type=scenario['alert_type'],
                severity=scenario['severity'],
                title=f"{'Risco aumentou' if scenario['alert_type'] == 'risk_increase' else 'Risco reduziu'} em {beach.name}",
                message=(
                    f"O nível de risco mudou de {scenario['previous_risk_level']} "
                    f"para {scenario['current_risk_level']}."
                ),
                reason_factors=scenario['reason_factors'],
                safety_tips=SAFETY_TIPS.get(current_level, []),
                previous_risk_level=scenario['previous_risk_level'],
                current_risk_level=scenario['current_risk_level'],
                nearest_safe_beach=nearest_safe,
                expires_at=now + timedelta(hours=6),
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(
            f"{created} alerta(s) de exemplo criado(s). "
            f"Teste com: GET /api/monitoring/alerts/"
        ))
