import requests

from apps.beaches.models import Beach

MARINE_API_URL = "https://marine-api.open-meteo.com/v1/marine"

HOURLY_VARS = "wave_height,wave_period,wave_direction,sea_surface_temperature"


def fetch_marine_conditions(beach):
    params = {
        "latitude": beach.latitude,
        "longitude": beach.longitude,
        "hourly": HOURLY_VARS,
        "forecast_days": 1,
        "timezone": "America/Recife",
    }

    response = requests.get(MARINE_API_URL, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])

    if not times:
        return None

    from datetime import datetime
    now = datetime.now()
    current_hour = now.strftime("%Y-%m-%dT%H:00")

    idx = 0
    for i, t in enumerate(times):
        if t >= current_hour:
            idx = i
            break

    def safe_get(key):
        values = hourly.get(key, [])
        if idx < len(values) and values[idx] is not None:
            return values[idx]
        return None

    return {
        "wave_height": safe_get("wave_height"),
        "wave_period": safe_get("wave_period"),
        "wave_direction": safe_get("wave_direction"),
        "sea_surface_temperature": safe_get("sea_surface_temperature"),
    }


def fetch_all_beaches_conditions():
    beaches = Beach.objects.all()
    results = {}

    for beach in beaches:
        try:
            conditions = fetch_marine_conditions(beach)
            if conditions:
                results[beach.id] = conditions
        except requests.RequestException:
            continue

    return results
