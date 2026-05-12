import pandas as pd
import numpy as np
from datetime import timedelta
from pathlib import Path

# ── Configurações ──────────────────────────────────────────────────────────────
_BASE      = Path(__file__).parent
INPUT_CSV  = _BASE / "dataset_meteorologia_enriquecido.csv"
OUTPUT_CSV = _BASE / "dataset_completo.csv"
REPORT_TXT = _BASE / "relatorio_negativos.txt"

# Ordem de deslocamentos em dias para tentar (positivo = futuro, negativo = passado)
DELTAS_DIAS = [180, -180, 90, -90, 270, -270, 365, -365]

# Colunas meteorológicas — preenchidas pela Open-Meteo se disponíveis
METEO_COLS = [
    "temp_max_C", "temp_min_C", "temp_media_C",
    "precipitacao_mm", "vento_max_kmh", "umidade_max_pct",
    "lat", "lon"
]

# Colunas que NÃO fazem sentido nos casos negativos (específicas do evento)
COLS_EVENTO = [
    "Case Number", "Case Number.1", "Case Number.2",
    "Name", "Age", "Injury", "Fatal (Y/N)",
    "Investigator or Source", "pdf", "href formula",
    "href", "Time", "Species ",
    "Unnamed: 9", "Unnamed: 23", "original order",
    "Nível da maré", "Clima no momento", "Temperatura do mar (°C)",
    "Activity_original",
]

# ── Funções auxiliares ─────────────────────────────────────────────────────────
def build_attack_keys(df: pd.DataFrame) -> set:
    """Constrói conjunto de chaves (Country|Area|Date) de todos os ataques."""
    return set(
        df.apply(
            lambda r: f"{r['Country']}|{r['Area']}|{r['Date'].date()}",
            axis=1
        )
    )


def gerar_negativo(row: pd.Series, nova_data: pd.Timestamp) -> dict:
    """
    Cria um dicionário representando o caso negativo,
    copiando campos estruturais e zerando campos de evento.
    """
    neg = {}

    # Campos que se mantêm iguais ao positivo de origem
    campos_manter = ["Country", "Area", "Location", "Activity", "Type",
                     "Year"] + METEO_COLS

    for col in campos_manter:
        neg[col] = row.get(col, np.nan)

    # Campos de evento ficam vazios — não faz sentido ter nome/lesão num não-ataque
    for col in COLS_EVENTO:
        neg[col] = np.nan

    # Data e ano atualizados
    neg["Date"]          = nova_data
    neg["Year"]          = nova_data.year
    neg["shark_attack"]  = 0   # ← label do modelo

    return neg


# ── Pipeline principal ─────────────────────────────────────────────────────────
def main():
    print(f"Carregando: {INPUT_CSV}")
    df = pd.read_csv(INPUT_CSV)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    # Garante colunas meteo existam (mesmo que vazias) se arquivo não for enriquecido
    for col in METEO_COLS:
        if col not in df.columns:
            df[col] = np.nan

    # Adiciona label positivo nos originais
    df["shark_attack"] = 1

    # Filtra positivos válidos para geração de negativos
    mask_valido = df["Date"].notna() & df["Year"].between(1940, 2025)
    df_valido   = df[mask_valido].copy()

    print(f"Positivos totais         : {len(df)}")
    print(f"Positivos válidos p/ geração: {len(df_valido)}")
    print(f"Positivos sem data válida: {(~mask_valido).sum()} (mantidos, sem negativo par)\n")

    # Constrói índice de ataques para evitar colisão
    attack_keys = build_attack_keys(df_valido)
    print(f"Chaves únicas de ataque  : {len(attack_keys)}")

    # ── Geração dos negativos ──────────────────────────────────────────────────
    negativos   = []
    sem_par     = 0
    delta_stats = {d: 0 for d in DELTAS_DIAS}

    for _, row in df_valido.iterrows():
        nova_data = None

        for delta in DELTAS_DIAS:
            candidata = row["Date"] + timedelta(days=delta)
            if not (1940 <= candidata.year <= 2025):
                continue
            key = f"{row['Country']}|{row['Area']}|{candidata.date()}"
            if key not in attack_keys:
                nova_data = candidata
                delta_stats[delta] += 1
                break

        if nova_data is None:
            sem_par += 1
            continue

        negativos.append(gerar_negativo(row, nova_data))

    print(f"\nNegativos gerados        : {len(negativos)}")
    print(f"Positivos sem par        : {sem_par}")

    # ── Monta dataset final ────────────────────────────────────────────────────
    df_neg = pd.DataFrame(negativos)

    # Garante mesmas colunas nos dois dataframes antes de concatenar
    for col in df.columns:
        if col not in df_neg.columns:
            df_neg[col] = np.nan
    df_neg = df_neg[df.columns]

    df_final = pd.concat([df, df_neg], ignore_index=True)

    # Ordena por Date para facilitar visualização
    df_final = df_final.sort_values("Date", na_position="last").reset_index(drop=True)

    df_final.to_csv(OUTPUT_CSV, index=False)
    print(f"\nDataset final salvo: {OUTPUT_CSV}")
    print(f"   Total de linhas      : {len(df_final)}")
    print(f"   Positivos (1)        : {(df_final['shark_attack']==1).sum()}")
    print(f"   Negativos (0)        : {(df_final['shark_attack']==0).sum()}")

    # ── Relatório ──────────────────────────────────────────────────────────────
    linhas_report = []
    linhas_report.append("=" * 55)
    linhas_report.append("  RELATÓRIO DE GERAÇÃO DE CASOS NEGATIVOS")
    linhas_report.append("=" * 55)
    linhas_report.append(f"\nArquivo de entrada  : {INPUT_CSV}")
    linhas_report.append(f"Arquivo de saída    : {OUTPUT_CSV}")
    linhas_report.append(f"\nPositivos totais    : {len(df)}")
    linhas_report.append(f"Positivos válidos   : {len(df_valido)}")
    linhas_report.append(f"Negativos gerados   : {len(negativos)}")
    linhas_report.append(f"Sem par (descartados): {sem_par}")
    linhas_report.append(f"\nTotal final         : {len(df_final)} linhas")
    linhas_report.append(f"  Positivos (1)     : {(df_final['shark_attack']==1).sum()}")
    linhas_report.append(f"  Negativos (0)     : {(df_final['shark_attack']==0).sum()}")

    linhas_report.append("\n── Deslocamentos utilizados ─────────────────────────")
    for delta, count in sorted(delta_stats.items(), key=lambda x: -x[1]):
        if count > 0:
            direcao = "futuro" if delta > 0 else "passado"
            linhas_report.append(f"  {abs(delta):>3} dias ({direcao:<7}): {count:>5} casos")

    linhas_report.append("\n── Distribuição dos negativos por país ──────────────")
    dist_pais = df_neg["Country"].value_counts()
    for pais, cnt in dist_pais.items():
        linhas_report.append(f"  {pais:<20}: {cnt:>5}")

    linhas_report.append("\n── Distribuição dos negativos por atividade ─────────")
    dist_act = df_neg["Activity"].value_counts()
    for act, cnt in dist_act.items():
        linhas_report.append(f"  {act:<25}: {cnt:>5}")

    linhas_report.append("\n── Nota metodológica ────────────────────────────────")
    linhas_report.append(
        "Os casos negativos foram gerados deslocando a data de cada\n"
        "ataque confirmado em ±180/90/270/365 dias, mantendo o mesmo\n"
        "local (Country + Area) e atividade. Apenas datas sem nenhum\n"
        "ataque registrado no dataset foram aceitas como negativas.\n"
        "Dados meteorológicos reais devem ser coletados via Open-Meteo\n"
        "para as datas geradas (use enriquecer_meteorologia.py)."
    )

    report = "\n".join(linhas_report)
    print("\n" + report)
    Path(REPORT_TXT).write_text(report, encoding="utf-8")
    print(f"\nRelatório salvo: {REPORT_TXT}")


if __name__ == "__main__":
    main()