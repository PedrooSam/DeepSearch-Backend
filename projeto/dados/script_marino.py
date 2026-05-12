import json
import time
import threading
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Configurações ─────────────────────────────────────────────────────────────
BASE       = Path(__file__).parent
INPUT_CSV  = BASE / "dataset_tratado_final.csv"
OUTPUT_CSV = BASE / "dataset_tratado_final.csv"
CACHE_FILE = BASE / "marino_cache.json"

MARINE_URL = "https://marine-api.open-meteo.com/v1/marine"

MARINE_VARS = {
    "wave_height_max": "altura_onda_m",
    "wave_period_max": "periodo_onda_s",
}

WORKERS = 10   # requisições paralelas — Open-Meteo suporta até ~10/s no free tier

# Deslocamentos (graus) para buscar ponto oceânico próximo quando coord cai em terra
OFFSETS = [
    (0.0,  0.0),
    (0.0,  0.1),  (0.0, -0.1),  ( 0.1, 0.0),  (-0.1, 0.0),
    (0.1,  0.1),  (0.1, -0.1),  (-0.1, 0.1),  (-0.1,-0.1),
    (0.0,  0.25), (0.0, -0.25), ( 0.25, 0.0), (-0.25, 0.0),
    (0.0,  0.5),  (0.0, -0.5),  ( 0.5, 0.0),  (-0.5, 0.0),
    (0.0,  1.0),  (0.0, -1.0),  ( 1.0, 0.0),  (-1.0, 0.0),
]

# Lock para acesso thread-safe ao cache
_cache_lock = threading.Lock()


# ── Cache ─────────────────────────────────────────────────────────────────────
def load_cache() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    return {}


def save_cache(cache: dict) -> None:
    with _cache_lock:
        CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")


# ── Chamada única à API ───────────────────────────────────────────────────────
def _call_api(lat: float, lon: float, date_str: str) -> dict | None:
    params = {
        "latitude":   round(lat, 4),
        "longitude":  round(lon, 4),
        "start_date": date_str,
        "end_date":   date_str,
        "daily":      list(MARINE_VARS.keys()),
        "timezone":   "auto",
    }
    try:
        resp = requests.get(MARINE_URL, params=params, timeout=15)
    except Exception:
        return None

    if resp.status_code >= 400:
        return None

    daily  = resp.json().get("daily", {})
    result = {}
    for api_key, col_name in MARINE_VARS.items():
        vals = daily.get(api_key, [None])
        result[col_name] = vals[0] if vals else None
    return result


def has_data(result) -> bool:
    return bool(result and any(v is not None for v in result.values()))


# ── Busca com fallback por deslocamento ───────────────────────────────────────
def fetch_one(key: str, lat: float, lon: float, date_str: str, cache: dict) -> dict | None:
    """Tenta coord original e deslocamentos até achar dado oceânico."""
    with _cache_lock:
        if key in cache and has_data(cache[key]):
            return cache[key]

    for dlat, dlon in OFFSETS:
        result = _call_api(lat + dlat, lon + dlon, date_str)
        if has_data(result):
            with _cache_lock:
                cache[key] = result
            return result

    with _cache_lock:
        cache[key] = None
    return None


# ── Pipeline principal ────────────────────────────────────────────────────────
def main():
    print("Carregando dataset...")
    df = pd.read_csv(INPUT_CSV)
    print(f"   {len(df)} linhas, {df.shape[1]} colunas")

    cache = load_cache()
    print(f"   Cache existente: {len(cache)} entradas\n")

    for col in MARINE_VARS.values():
        if col not in df.columns:
            df[col] = None

    mask = df["lat"].notna() & df["lon"].notna() & df["Date"].notna()
    subset = df[mask].copy()
    subset["_date_str"] = subset["Date"].astype(str).str[:10]
    subset["_key"]      = subset["lat"].astype(str) + "," + subset["lon"].astype(str) + "," + subset["_date_str"]

    # ── Deduplicar: só busca cada (lat, lon, data) única uma vez ──────────────
    unique_keys = subset[["_key", "lat", "lon", "_date_str"]].drop_duplicates("_key")
    # Filtra as que ainda não estão no cache com dados
    pending = unique_keys[~unique_keys["_key"].apply(lambda k: has_data(cache.get(k)))]
    print(f"Linhas com coordenadas: {len(subset)}")
    print(f"   Combinações únicas    : {len(unique_keys)}")
    print(f"   Já no cache           : {len(unique_keys) - len(pending)}")
    print(f"   A buscar agora        : {len(pending)}\n")

    results_map: dict[str, dict | None] = {}

    # ── Requisições paralelas ─────────────────────────────────────────────────
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {
            executor.submit(fetch_one, row["_key"], row["lat"], row["lon"], row["_date_str"], cache): row["_key"]
            for _, row in pending.iterrows()
        }

        done = 0
        with tqdm(total=len(futures), desc="Marine API") as pbar:
            for future in as_completed(futures):
                key    = futures[future]
                result = future.result()
                results_map[key] = result
                done += 1
                pbar.update(1)

                if done % 100 == 0:
                    save_cache(cache)

    save_cache(cache)

    # ── Aplicar resultados ao dataframe ───────────────────────────────────────
    sucesso = sem_cobertura = 0
    for idx, row in subset.iterrows():
        result = cache.get(row["_key"])
        if has_data(result):
            for col, val in result.items():
                df.at[idx, col] = val
            sucesso += 1
        else:
            sem_cobertura += 1

    print(f"\nLinhas com dados marinhos : {sucesso}")
    print(f"Sem cobertura marinha     : {sem_cobertura}")
    print("\nCobertura final:")
    for col in MARINE_VARS.values():
        n = df[col].notna().sum()
        print(f"  {col:<22} {n:>5} / {len(df)}  ({100*n/len(df):.1f}%)")

    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\nDataset salvo em: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
