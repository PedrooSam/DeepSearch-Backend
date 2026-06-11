import math
from datetime import timedelta

from django.utils import timezone

from apps.beaches.models import Beach
from apps.risk.models import RiskPrediction
from .models import Alert


SAFETY_TIPS = {
    'Alto': [
        'Evite entrar na água neste momento',
        'Procure uma praia segura próxima',
    ],
    'Moderado': [
        'Tenha cuidado extra ao entrar no mar',
        'Não se afaste da costa',
    ],
    'Baixo': [
        'Condições favoráveis para banho',
        'Siga as precauções normais',
    ],
    'Muito baixo': [
        'Condições seguras para banho',
    ],
}

COOLDOWN_HOURS = 2
ALERT_EXPIRY_HOURS = 6


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def find_nearest_safe_beach(beach, all_beaches_with_risk):
    safe_levels = ('Baixo', 'Muito baixo')
    nearest = None
    min_dist = float('inf')

    for other_beach, risk_level in all_beaches_with_risk:
        if other_beach.id == beach.id:
            continue
        if risk_level not in safe_levels:
            continue
        dist = haversine_km(
            beach.latitude, beach.longitude,
            other_beach.latitude, other_beach.longitude,
        )
        if dist < min_dist:
            min_dist = dist
            nearest = other_beach

    return nearest


def has_recent_alert(beach):
    cutoff = timezone.now() - timedelta(hours=COOLDOWN_HOURS)
    return Alert.objects.filter(beach=beach, created_at__gte=cutoff).exists()


RISK_ORDER = ['Muito baixo', 'Baixo', 'Moderado', 'Alto']


def detect_risk_change(beach, current_risk_level):
    last_prediction = (
        RiskPrediction.objects.filter(beach=beach)
        .order_by('-generated_at')
        .first()
    )

    if not last_prediction:
        return None

    previous_level = last_prediction.risk_level

    if previous_level == current_risk_level:
        return None

    prev_idx = RISK_ORDER.index(previous_level) if previous_level in RISK_ORDER else -1
    curr_idx = RISK_ORDER.index(current_risk_level) if current_risk_level in RISK_ORDER else -1

    if prev_idx == -1 or curr_idx == -1:
        return None

    alert_type = 'risk_increase' if curr_idx > prev_idx else 'risk_decrease'

    return {
        'previous_level': previous_level,
        'current_level': current_risk_level,
        'alert_type': alert_type,
    }


def calc_severity(alert_type, current_level):
    if alert_type == 'risk_increase' and current_level == 'Alto':
        return 'high'
    if alert_type == 'risk_increase':
        return 'medium'
    return 'low'


def generate_alert(beach, change_data, factors, all_beaches_with_risk):
    if has_recent_alert(beach):
        return None

    alert_type = change_data['alert_type']
    current_level = change_data['current_level']
    previous_level = change_data['previous_level']
    severity = calc_severity(alert_type, current_level)

    if alert_type == 'risk_increase':
        title = f"Risco aumentou em {beach.name}"
        message = (
            f"O nível de risco mudou de {previous_level} para {current_level}. "
            f"Tome precauções."
        )
    else:
        title = f"Risco reduziu em {beach.name}"
        message = (
            f"O nível de risco baixou de {previous_level} para {current_level}."
        )

    nearest_safe = None
    if current_level in ('Alto', 'Moderado'):
        nearest_safe = find_nearest_safe_beach(beach, all_beaches_with_risk)

    alert = Alert.objects.create(
        beach=beach,
        alert_type=alert_type,
        severity=severity,
        title=title,
        message=message,
        reason_factors=factors,
        safety_tips=SAFETY_TIPS.get(current_level, []),
        previous_risk_level=previous_level,
        current_risk_level=current_level,
        nearest_safe_beach=nearest_safe,
        expires_at=timezone.now() + timedelta(hours=ALERT_EXPIRY_HOURS),
    )

    return alert


def get_nearby_alerts(lat, lon, radius_km=5):
    active_alerts = Alert.objects.filter(expires_at__gte=timezone.now())
    nearby = []

    for alert in active_alerts.select_related('beach', 'nearest_safe_beach'):
        dist = haversine_km(lat, lon, alert.beach.latitude, alert.beach.longitude)
        if dist <= radius_km:
            nearby.append(alert)

    return nearby
