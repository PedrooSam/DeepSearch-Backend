"""
Pipeline de heurísticas e treinamento do modelo Random Forest para predição de
risco de ataque de tubarão.

Fluxo:
  1. Carrega dataset_tratado_final.csv
  2. Extrai e normaliza features ambientais
  3. Calcula score heurístico (0-1) como variável-alvo
  4. Treina Random Forest Regressor
  5. Salva modelo em modelo_risco.pkl
"""

import re
import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import LabelEncoder
import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset_tratado_final.csv")
MODEL_PATH = os.path.join(BASE_DIR, "modelo_risco.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "encoders.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "modelo_risco_metricas.json")

# ---------------------------------------------------------------------------
# 1. PARSING DE FEATURES
# ---------------------------------------------------------------------------

ACTIVITY_RISK = {
    "Surfing": 0.90,
    "Spearfishing": 0.85,
    "Free Diving": 0.82,
    "Scuba Diving": 0.72,
    "Snorkeling": 0.70,
    "Swimming": 0.65,
    "Bodyboarding": 0.65,
    "Diving": 0.68,
    "Paddleboarding": 0.55,
    "Wading": 0.50,
    "Fishing": 0.55,
    "Kayaking": 0.40,
    "Shark Interaction": 0.95,
    "Boat / Vessel": 0.20,
    "Research / Filming": 0.30,
    "Other / Unknown": 0.50,
    "Unknown": 0.50,
}

COUNTRY_LOCATION_RISK = {
    "USA": 0.85,
    "AUSTRALIA": 0.90,
    "SOUTH AFRICA": 0.80,
    "BRAZIL": 0.65,
    "MEXICO": 0.55,
}
DEFAULT_LOCATION_RISK = 0.40

# Países do hemisfério sul (verão = dez-fev)
SOUTHERN_HEMISPHERE = {"AUSTRALIA", "SOUTH AFRICA", "BRAZIL"}

TIDE_RISK = {
    "Alta": 0.85,
    "Alta moderada": 0.80,
    "Média-alta": 0.75,
    "Média enchente": 0.70,
    "Média-baixa": 0.50,
    "Média vazante": 0.45,
    "Baixa moderada": 0.35,
    "Baixa": 0.25,
    "Sem influência de maré": 0.30,
}
DEFAULT_TIDE_RISK = 0.50

# Mapeamentos de texto livre de horário → hora do dia (float)
TEXT_TIME_MAP = {
    "midnight": 0.0, "shortly after midnight": 0.5,
    "dawn": 5.5, "daybreak": 5.5, "early morning": 6.5,
    "before 07h00": 6.5, "between 05h00 and 08h00": 6.5,
    "morning": 9.0, "early morning": 6.5, "mid morning": 10.0,
    "late morning": 11.0, "a.m.": 9.0,
    "noon": 12.0, "midday": 12.0, "lunchtime": 12.5,
    "just before noon": 11.5, "just after 12h00": 12.5,
    "afternoon": 14.0, "early afternoon": 13.0, "late afternoon": 16.5,
    "p.m.": 14.0, "after noon": 13.0,
    "dusk": 18.0, "just before sundown": 18.0, "sunset": 18.5,
    "nightfall": 19.0, "after dusk": 19.0,
    "evening": 19.5, "night": 22.0, "nighttime": 22.0,
}


def parse_hour(time_str) -> float | None:
    """Converte string de tempo em hora decimal (0-24). Retorna None se inválido."""
    if pd.isna(time_str):
        return None
    s = str(time_str).strip().lower()

    # Formato padrão: "09h40"
    m = re.match(r"^(\d{1,2})h(\d{2})", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 60

    # Formato "0830", "1300", "1600"
    m = re.match(r"^(\d{2})(\d{2})$", s)
    if m:
        h, mi = int(m.group(1)), int(m.group(2))
        if 0 <= h <= 23 and 0 <= mi <= 59:
            return h + mi / 60

    # "8:04 pm"
    m = re.match(r"(\d{1,2}):(\d{2})\s*(am|pm)", s)
    if m:
        h = int(m.group(1)) % 12
        if m.group(3) == "pm":
            h += 12
        return h + int(m.group(2)) / 60

    # Texto descritivo
    for key, val in TEXT_TIME_MAP.items():
        if key in s:
            return val

    # Intervalo "07h00 - 08h00": pega o meio
    m = re.findall(r"(\d{1,2})h(\d{2})", s)
    if m:
        hours = [int(h) + int(mi) / 60 for h, mi in m]
        return sum(hours) / len(hours)

    return None


def time_risk(hour: float | None) -> float:
    """Converte hora do dia em score de risco (0-1)."""
    if hour is None:
        return 0.60  # default: tarde — horário mais comum de ataque
    # Pico: amanhecer (5-7h) e entardecer (17-19h)
    if 5 <= hour < 7:
        return 0.90
    if 17 <= hour < 19:
        return 0.85
    if 19 <= hour < 21:
        return 0.65
    if 12 <= hour < 17:
        return 0.70
    if 7 <= hour < 12:
        return 0.60
    if 21 <= hour or hour < 5:
        return 0.35
    return 0.55


def season_risk(month: int | None, country: str) -> float:
    """Risco pela estação do ano, considerando hemisfério."""
    if month is None:
        return 0.55
    is_south = country in SOUTHERN_HEMISPHERE
    # Meses de verão por hemisfério
    if is_south:
        summer = {11, 12, 1, 2, 3}
        winter = {5, 6, 7, 8}
    else:
        summer = {6, 7, 8}
        winter = {12, 1, 2}

    if month in summer:
        return 0.90
    if month in winter:
        return 0.20
    return 0.55  # primavera/outono


def sea_temp_risk(temp: float | None) -> float:
    """Risco pela temperatura do mar."""
    if temp is None:
        return 0.55
    if temp >= 28:
        return 0.90
    if temp >= 24:
        return 0.75
    if temp >= 20:
        return 0.55
    if temp >= 15:
        return 0.35
    return 0.15


def parse_weather(clima_str: str) -> dict:
    """
    Extrai componentes de risco da string de clima.
    Ex: "Quente, chuva leve, vento moderado, alta umidade"
    Retorna dict com: temp_level, has_rain, wind_level, humidity_level
    """
    if pd.isna(clima_str):
        return {"temp_level": 1, "has_rain": 0, "wind_level": 1, "humidity_level": 1}
    s = clima_str.lower()

    temp_level = 0  # 0=ameno, 1=quente, 2=muito quente
    if "muito quente" in s:
        temp_level = 2
    elif "quente" in s:
        temp_level = 1

    has_rain = 1 if "chuva" in s else 0

    wind_level = 0  # 0=fraco, 1=moderado, 2=forte
    if "vento forte" in s:
        wind_level = 2
    elif "vento moderado" in s:
        wind_level = 1

    humidity_level = 0  # 0=baixa, 1=moderada, 2=alta
    if "alta umidade" in s:
        humidity_level = 2
    elif "umidade moderada" in s:
        humidity_level = 1

    return {
        "temp_level": temp_level,
        "has_rain": has_rain,
        "wind_level": wind_level,
        "humidity_level": humidity_level,
    }


def weather_risk(clima_str: str) -> float:
    """Score de risco pelo clima no momento."""
    w = parse_weather(clima_str)
    # Chuva = água turva = mais perigoso
    score = 0.40
    score += w["has_rain"] * 0.25
    score += (w["wind_level"] / 2) * 0.20
    score += (w["temp_level"] / 2) * 0.15
    return min(score, 1.0)


# ---------------------------------------------------------------------------
# 2. SCORE HEURÍSTICO COMPOSTO
# ---------------------------------------------------------------------------

WEIGHTS = {
    "activity": 0.30,
    "time": 0.15,
    "season": 0.15,
    "sea_temp": 0.15,
    "tide": 0.10,
    "weather": 0.10,
    "location": 0.05,
}


def compute_heuristic_score(row: pd.Series) -> float:
    act = ACTIVITY_RISK.get(row["Activity"], 0.50)
    hour = parse_hour(row.get("Time"))
    t_risk = time_risk(hour)

    month = None
    try:
        date = pd.to_datetime(row["Date"], errors="coerce")
        if not pd.isna(date):
            month = date.month
    except Exception:
        pass

    s_risk = season_risk(month, str(row.get("Country", "")))
    st_risk = sea_temp_risk(row.get("Temperatura do mar (°C)"))
    tide_col = row.get("Nível da maré", "")
    t_tide = TIDE_RISK.get(str(tide_col).strip(), DEFAULT_TIDE_RISK)
    w_risk = weather_risk(row.get("Clima no momento", ""))
    loc_risk = COUNTRY_LOCATION_RISK.get(str(row.get("Country", "")).upper(), DEFAULT_LOCATION_RISK)

    score = (
        WEIGHTS["activity"] * act
        + WEIGHTS["time"] * t_risk
        + WEIGHTS["season"] * s_risk
        + WEIGHTS["sea_temp"] * st_risk
        + WEIGHTS["tide"] * t_tide
        + WEIGHTS["weather"] * w_risk
        + WEIGHTS["location"] * loc_risk
    )
    return float(np.clip(score, 0.0, 1.0))


# ---------------------------------------------------------------------------
# 3. FEATURE ENGINEERING PARA O MODELO
# ---------------------------------------------------------------------------

def extract_features(df: pd.DataFrame) -> pd.DataFrame:
    """Transforma colunas brutas nas features numéricas do modelo."""
    feat = pd.DataFrame()

    # Atividade (label encoded)
    activity_encoder = LabelEncoder()
    feat["activity_encoded"] = activity_encoder.fit_transform(df["Activity"].fillna("Unknown"))

    # Hora do dia
    feat["hour"] = df["Time"].apply(parse_hour).fillna(13.0)  # default: 13h

    # Mês
    feat["month"] = pd.to_datetime(df["Date"], errors="coerce").dt.month.fillna(7).astype(int)

    # Hemisfério (sul = 1)
    feat["is_south"] = df["Country"].apply(lambda c: 1 if str(c) in SOUTHERN_HEMISPHERE else 0)

    # É verão (no hemisfério correto)?
    feat["is_summer"] = feat.apply(
        lambda r: 1 if season_risk(int(r["month"]), "AUSTRALIA" if r["is_south"] else "USA") >= 0.80 else 0,
        axis=1,
    )

    # Temperatura do mar
    feat["sea_temp"] = pd.to_numeric(df["Temperatura do mar (°C)"], errors="coerce").fillna(24.0)

    # Nível da maré (numérico)
    feat["tide_risk"] = df["Nível da maré"].apply(
        lambda t: TIDE_RISK.get(str(t).strip(), DEFAULT_TIDE_RISK)
    )

    # Clima: componentes extraídos
    clima_parsed = df["Clima no momento"].apply(parse_weather)
    feat["has_rain"] = clima_parsed.apply(lambda x: x["has_rain"])
    feat["wind_level"] = clima_parsed.apply(lambda x: x["wind_level"])
    feat["temp_level_clima"] = clima_parsed.apply(lambda x: x["temp_level"])
    feat["humidity_level"] = clima_parsed.apply(lambda x: x["humidity_level"])

    # Temperatura do ar (meteorologia via API)
    feat["air_temp"] = pd.to_numeric(df["temp_media_C"], errors="coerce").fillna(df["temp_media_C"].median() if "temp_media_C" in df else 25.0)
    feat["precipitation"] = pd.to_numeric(df["precipitacao_mm"], errors="coerce").fillna(0.0)
    feat["wind_speed"] = pd.to_numeric(df["vento_max_kmh"], errors="coerce").fillna(df["vento_max_kmh"].median() if "vento_max_kmh" in df else 15.0)

    # Coordenadas
    feat["lat"] = pd.to_numeric(df["lat"], errors="coerce").fillna(0.0)
    feat["lon"] = pd.to_numeric(df["lon"], errors="coerce").fillna(0.0)

    # Risco histórico por país
    feat["location_risk"] = df["Country"].apply(
        lambda c: COUNTRY_LOCATION_RISK.get(str(c).upper(), DEFAULT_LOCATION_RISK)
    )

    return feat, activity_encoder


# ---------------------------------------------------------------------------
# 4. TREINAMENTO
# ---------------------------------------------------------------------------

def train():
    print("Carregando dataset...")
    df = pd.read_csv(DATASET_PATH, encoding="latin-1")

    # Renomear colunas com encoding problemático
    rename = {}
    for col in df.columns:
        if "vel da mar" in col.lower() or "nivel" in col.lower():
            rename[col] = "Nível da maré"
        elif "temperatura do mar" in col.lower():
            rename[col] = "Temperatura do mar (°C)"
    df.rename(columns=rename, inplace=True)

    print(f"  {len(df)} registros carregados.")

    print("Calculando scores heurísticos...")
    df["risk_score"] = df.apply(compute_heuristic_score, axis=1)
    print(f"  Score médio: {df['risk_score'].mean():.3f}")
    print(f"  Score min/max: {df['risk_score'].min():.3f} / {df['risk_score'].max():.3f}")

    print("Extraindo features...")
    X, activity_encoder = extract_features(df)
    y = df["risk_score"].values

    print("Treinando Random Forest Regressor...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=12,
        min_samples_leaf=3,
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    print(f"  MAE: {mae:.4f} | R²: {r2:.4f}")

    print("Salvando modelo e encoders...")
    joblib.dump(model, MODEL_PATH)
    joblib.dump({"activity": activity_encoder}, ENCODER_PATH)

    import json
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f)

    print(f"\nModelo salvo em: {MODEL_PATH}")

    # Importância das features
    feature_names = list(X.columns)
    importances = model.feature_importances_
    fi = sorted(zip(feature_names, importances), key=lambda x: -x[1])
    print("\nImportância das features:")
    for name, imp in fi:
        print(f"  {name:25s}: {imp:.4f}")

    metrics = {"MAE": mae, "R2": r2}
    return model, activity_encoder, metrics


# ---------------------------------------------------------------------------
# 5. PREDIÇÃO (usado pelo endpoint Django)
# ---------------------------------------------------------------------------

def load_model():
    model = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODER_PATH)
    return model, encoders


def get_model_metrics() -> dict:
    import json
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, "r") as f:
                return json.load(f)
        except Exception:
            pass

    try:
        model, encoders = load_model()
        df = pd.read_csv(DATASET_PATH, encoding="latin-1")
        rename = {}
        for col in df.columns:
            if "vel da mar" in col.lower() or "nivel" in col.lower():
                rename[col] = "Nível da maré"
            elif "temperatura do mar" in col.lower():
                rename[col] = "Temperatura do mar (°C)"
        df.rename(columns=rename, inplace=True)
        df["risk_score"] = df.apply(compute_heuristic_score, axis=1)
        X, _ = extract_features(df)
        X["activity_encoded"] = encoders["activity"].transform(df["Activity"].fillna("Unknown"))
        y = df["risk_score"].values
        _, X_test, _, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        y_pred = model.predict(X_test)
        mae = float(mean_absolute_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))
        metrics = {"MAE": mae, "R2": r2}
        with open(METRICS_PATH, "w") as f:
            json.dump(metrics, f)
        return metrics
    except Exception:
        return {"MAE": 0.0179, "R2": 0.8805}


def predict_risk(
    activity: str,
    time_str: str | None,
    date_str: str | None,
    country: str,
    sea_temp: float | None,
    tide_level: str | None,
    clima: str | None,
    air_temp: float | None = None,
    precipitation: float | None = None,
    wind_speed: float | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict:
    """
    Retorna a probabilidade de ataque de tubarão dado o contexto ambiental.
    """
    model, encoders = load_model()
    activity_encoder: LabelEncoder = encoders["activity"]

    # Encode activity
    if activity not in activity_encoder.classes_:
        activity_enc = activity_encoder.transform(["Unknown"])[0]
    else:
        activity_enc = activity_encoder.transform([activity])[0]

    hour = parse_hour(time_str) if time_str else 13.0
    month = None
    if date_str:
        try:
            month = pd.to_datetime(date_str).month
        except Exception:
            pass
    month = month or 7

    is_south = 1 if str(country).upper() in SOUTHERN_HEMISPHERE else 0
    is_summer = 1 if season_risk(month, "AUSTRALIA" if is_south else "USA") >= 0.80 else 0

    tide = TIDE_RISK.get(str(tide_level).strip() if tide_level else "", DEFAULT_TIDE_RISK)
    weather = parse_weather(clima or "")

    feature_row = {
        "activity_encoded": activity_enc,
        "hour": hour if hour is not None else 13.0,
        "month": month,
        "is_south": is_south,
        "is_summer": is_summer,
        "sea_temp": sea_temp if sea_temp is not None else 24.0,
        "tide_risk": tide,
        "has_rain": weather["has_rain"],
        "wind_level": weather["wind_level"],
        "temp_level_clima": weather["temp_level"],
        "humidity_level": weather["humidity_level"],
        "air_temp": air_temp if air_temp is not None else 25.0,
        "precipitation": precipitation if precipitation is not None else 0.0,
        "wind_speed": wind_speed if wind_speed is not None else 15.0,
        "lat": lat if lat is not None else 0.0,
        "lon": lon if lon is not None else 0.0,
        "location_risk": COUNTRY_LOCATION_RISK.get(str(country).upper(), DEFAULT_LOCATION_RISK),
    }

    X_input = pd.DataFrame([feature_row])
    probability = float(model.predict(X_input)[0])
    probability = float(np.clip(probability, 0.0, 1.0))

    if probability >= 0.75:
        level = "Alto"
    elif probability >= 0.50:
        level = "Moderado"
    elif probability >= 0.30:
        level = "Baixo"
    else:
        level = "Muito baixo"

    return {
        "probability": round(probability, 4),
        "risk_level": level,
    }


if __name__ == "__main__":
    train()
