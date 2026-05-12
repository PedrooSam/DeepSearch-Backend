import json
import time
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# ── Configurações ─────────────────────────────────────────────────────────────
_BASE       = Path(__file__).parent
INPUT_CSV   = _BASE / "dataset_padronizado.csv"
OUTPUT_CSV  = _BASE / "dataset_meteorologia_enriquecido.csv"
GEO_CACHE   = _BASE / "geocode_cache.json"
MET_CACHE   = _BASE / "meteo_cache.json"

# Open-Meteo: dados disponíveis a partir de 1940
ANO_MIN = 1940
ANO_MAX = 2025

# Colunas meteorológicas que a Open-Meteo retorna (nome interno → nome final)
METEO_VARS = {
    "temperature_2m_max":          "temp_max_C",
    "temperature_2m_min":          "temp_min_C",
    "precipitation_sum":           "precipitacao_mm",
    "wind_speed_10m_max":          "vento_max_kmh",
    "relative_humidity_2m_max":    "umidade_max_pct",
}

# ── Geocodificação ────────────────────────────────────────────────────────────
geolocator = Nominatim(user_agent="shark_attack_research_v1", timeout=10)

def build_query(row: pd.Series) -> str:
    """Monta a string de busca mais específica possível."""
    parts = []
    if pd.notna(row.get("Location")) and str(row["Location"]).strip():
        parts.append(str(row["Location"]).strip())
    if pd.notna(row.get("Area")) and str(row["Area"]).strip():
        parts.append(str(row["Area"]).strip())
    if pd.notna(row.get("Country")) and str(row["Country"]).strip():
        parts.append(str(row["Country"]).strip())
    return ", ".join(parts)


def geocode(query: str, cache: dict) -> tuple[float, float] | None:
    """Retorna (lat, lon) para uma string de localização, com cache."""
    if not query:
        return None

    if query in cache:
        return cache[query]  # pode ser None se já tentamos e falhou

    try:
        time.sleep(1.1)  # respeita o rate-limit do Nominatim (1 req/s)
        loc = geolocator.geocode(query, language="en")
        if loc:
            result = (round(loc.latitude, 4), round(loc.longitude, 4))
        else:
            # Tenta query mais genérica (sem o Location específico)
            parts = [p.strip() for p in query.split(",")]
            if len(parts) > 1:
                fallback = ", ".join(parts[1:])
                time.sleep(1.1)
                loc2 = geolocator.geocode(fallback, language="en")
                result = (round(loc2.latitude, 4), round(loc2.longitude, 4)) if loc2 else None
            else:
                result = None
    except (GeocoderTimedOut, GeocoderServiceError):
        result = None

    cache[query] = result
    return result


# ── Open-Meteo ────────────────────────────────────────────────────────────────
METEO_URL = "https://archive-api.open-meteo.com/v1/archive"

def fetch_meteo(lat: float, lon: float, date_str: str, cache: dict) -> dict | None:
    """
    Busca dados meteorológicos diários para lat/lon/data.
    Retorna dict com as variáveis ou None em caso de falha.
    """
    key = f"{lat},{lon},{date_str}"
    if key in cache:
        return cache[key]

    params = {
        "latitude":   lat,
        "longitude":  lon,
        "start_date": date_str,
        "end_date":   date_str,
        "daily":      ",".join(METEO_VARS.keys()),
        "timezone":   "auto",
        "wind_speed_unit": "kmh",
    }

    try:
        time.sleep(0.15)  # ~6 req/s — Open-Meteo permite até 10/s no free tier
        resp = requests.get(METEO_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        daily = data.get("daily", {})
        result = {}
        for api_key, col_name in METEO_VARS.items():
            vals = daily.get(api_key, [None])
            result[col_name] = vals[0] if vals else None

        # Temperatura média
        tmax = result.get("temp_max_C")
        tmin = result.get("temp_min_C")
        result["temp_media_C"] = round((tmax + tmin) / 2, 1) if (tmax is not None and tmin is not None) else None

    except Exception:
        result = None

    cache[key] = result
    return result


# ── Pipeline principal ────────────────────────────────────────────────────────
def main():
    # Carrega dataset
    df = pd.read_csv(INPUT_CSV)
    print(f"Dataset carregado: {len(df)} linhas, {df.shape[1]} colunas")

    # Filtra apenas linhas aproveitáveis pela API
    mask_valido = (
        df["Year"].between(ANO_MIN, ANO_MAX) &
        df["Date"].notna()
    )
    print(f"Linhas aproveitáveis (data válida + ano {ANO_MIN}-{ANO_MAX}): {mask_valido.sum()}")
    print(f"Linhas que ficarão sem dados meteorológicos: {(~mask_valido).sum()}\n")

    # Carrega caches (ou cria novos)
    geo_cache  = json.loads(Path(GEO_CACHE).read_text())  if Path(GEO_CACHE).exists()  else {}
    met_cache  = json.loads(Path(MET_CACHE).read_text())  if Path(MET_CACHE).exists()  else {}

    # Inicializa colunas de saída
    new_cols = list(METEO_VARS.values()) + ["temp_media_C", "lat", "lon"]
    for col in new_cols:
        if col not in df.columns:
            df[col] = None

    # ── Etapa 1: Geocodificação ───────────────────────────────────────────────
    print("── Etapa 1: Geocodificação ──────────────────────────────────────")
    queries = df[mask_valido].apply(build_query, axis=1)
    unique_queries = queries.unique()
    print(f"Localizações únicas a geocodificar: {len(unique_queries)}")

    for q in tqdm(unique_queries, desc="Geocodificando"):
        if q not in geo_cache:
            geo_cache[q] = geocode(q, geo_cache)

    # Salva cache intermediário
    Path(GEO_CACHE).write_text(json.dumps(geo_cache, ensure_ascii=False, indent=2))

    # Aplica coordenadas ao dataframe
    def safe_lat(q):
        r = geo_cache.get(q)
        return r[0] if isinstance(r, (list, tuple)) and len(r) == 2 else None

    def safe_lon(q):
        r = geo_cache.get(q)
        return r[1] if isinstance(r, (list, tuple)) and len(r) == 2 else None

    df.loc[mask_valido, "lat"] = queries.map(safe_lat).values
    df.loc[mask_valido, "lon"] = queries.map(safe_lon).values

    geo_ok = df.loc[mask_valido, "lat"].notna().sum()
    print(f"Geocodificação bem-sucedida: {geo_ok}/{mask_valido.sum()} ({100*geo_ok/mask_valido.sum():.1f}%)\n")

    # ── Etapa 2: Dados meteorológicos ─────────────────────────────────────────
    print("── Etapa 2: Dados meteorológicos (Open-Meteo) ───────────────────")
    mask_com_geo = mask_valido & df["lat"].notna()
    print(f"Linhas com coordenadas válidas: {mask_com_geo.sum()}")

    sucesso = 0
    for idx, row in tqdm(df[mask_com_geo].iterrows(), total=mask_com_geo.sum(), desc="Open-Meteo"):
        date_str = str(row["Date"])[:10]  # garante formato YYYY-MM-DD
        meteo = fetch_meteo(row["lat"], row["lon"], date_str, met_cache)

        if meteo:
            for col, val in meteo.items():
                df.at[idx, col] = val
            sucesso += 1

    # Salva cache meteorológico
    Path(MET_CACHE).write_text(json.dumps(met_cache, ensure_ascii=False, indent=2))

    print(f"Dados meteorológicos coletados: {sucesso}/{mask_com_geo.sum()} ({100*sucesso/max(mask_com_geo.sum(),1):.1f}%)\n")

    # ── Relatório final ───────────────────────────────────────────────────────
    print("── Relatório de cobertura ───────────────────────────────────────")
    for col in new_cols:
        preench = df[col].notna().sum()
        print(f"  {col:<25} {preench:>5} / {len(df)} ({100*preench/len(df):.1f}%)")

    # Salva dataset final
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅  Dataset salvo em: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()