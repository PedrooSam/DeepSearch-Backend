"""
Avaliação visual do modelo Random Forest de predição de risco de ataque de tubarão.

Métricas calculadas:
  MAE, MSE, RMSE, R², MAPE, Explained Variance Score

Plots gerados (figura única 2×3):
  1. Predito vs Real
  2. Resíduos vs Predito
  3. Distribuição dos resíduos
  4. Q-Q Plot dos resíduos
  5. Importância das features
  6. CDF do erro absoluto

Saída: avaliacao_modelo.png
"""

import os
import sys
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.lines import Line2D
import scipy.stats as stats
import joblib

from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    explained_variance_score,
)

# Importa o módulo de heurísticas do mesmo diretório
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import heuristicas

MODEL_PATH = os.path.join(BASE_DIR, "modelo_risco.pkl")
ENCODER_PATH = os.path.join(BASE_DIR, "encoders.pkl")
DATASET_PATH = os.path.join(BASE_DIR, "dataset_tratado_final.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "avaliacao_modelo.png")

PALETTE = {
    "primary": "#1B4F72",
    "accent": "#E74C3C",
    "success": "#27AE60",
    "warn": "#F39C12",
    "light": "#AED6F1",
    "grid": "#EAECEE",
    "bg": "#FDFEFE",
}


# ---------------------------------------------------------------------------
# REPRODUÇÃO DO PIPELINE DE TREINAMENTO
# ---------------------------------------------------------------------------

def load_and_prepare():
    """Reproduz o pipeline de dados com o mesmo split e encoder do treinamento."""
    df = pd.read_csv(DATASET_PATH, encoding="latin-1")

    rename = {}
    for col in df.columns:
        if "vel da mar" in col.lower() or "nivel" in col.lower():
            rename[col] = "Nível da maré"
        elif "temperatura do mar" in col.lower():
            rename[col] = "Temperatura do mar (°C)"
    df.rename(columns=rename, inplace=True)

    df["risk_score"] = df.apply(heuristicas.compute_heuristic_score, axis=1)

    # Usa o encoder salvo para garantir consistência com o modelo em produção
    encoders = joblib.load(ENCODER_PATH)
    saved_encoder = encoders["activity"]

    X, _ = heuristicas.extract_features(df)
    # Substitui a coluna activity_encoded pelo encoder salvo (evita divergência)
    X["activity_encoded"] = saved_encoder.transform(df["Activity"].fillna("Unknown"))

    y = df["risk_score"].values

    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, df.index, test_size=0.2, random_state=42
    )

    df_test = df.loc[idx_test].reset_index(drop=True)

    return X_train, X_test, y_train, y_test, df_test, list(X.columns)


# ---------------------------------------------------------------------------
# MÉTRICAS
# ---------------------------------------------------------------------------

def calculate_metrics(y_true, y_pred, label="Teste"):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    r2 = r2_score(y_true, y_pred)
    evs = explained_variance_score(y_true, y_pred)

    mask = y_true != 0
    mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100

    return {
        "label": label,
        "MAE": mae,
        "MSE": mse,
        "RMSE": rmse,
        "R²": r2,
        "MAPE (%)": mape,
        "Explained Variance": evs,
    }


def print_metrics(metrics_train, metrics_test):
    print("\n" + "=" * 52)
    print(f"{'Métrica':<22} {'Treino':>12} {'Teste':>12}")
    print("=" * 52)
    keys = ["MAE", "MSE", "RMSE", "R²", "MAPE (%)", "Explained Variance"]
    for k in keys:
        print(f"{k:<22} {metrics_train[k]:>12.4f} {metrics_test[k]:>12.4f}")
    print("=" * 52)


# ---------------------------------------------------------------------------
# PLOTS
# ---------------------------------------------------------------------------

def setup_ax(ax, title, xlabel, ylabel):
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8, color="#2C3E50")
    ax.set_xlabel(xlabel, fontsize=9, color="#5D6D7E")
    ax.set_ylabel(ylabel, fontsize=9, color="#5D6D7E")
    ax.set_facecolor(PALETTE["bg"])
    ax.grid(True, color=PALETTE["grid"], linewidth=0.8, linestyle="--", alpha=0.7)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8, colors="#5D6D7E")


def plot_predicted_vs_actual(ax, y_true, y_pred, metrics):
    """1. Scatter Predito vs Real com linha de identidade."""
    residuals = y_true - y_pred
    colors = np.abs(residuals)

    sc = ax.scatter(
        y_true, y_pred,
        c=colors, cmap="RdYlGn_r",
        alpha=0.55, s=18, edgecolors="none",
        vmin=0, vmax=colors.max(),
    )

    lo, hi = min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())
    margin = (hi - lo) * 0.03
    lims = [lo - margin, hi + margin]
    ax.plot(lims, lims, "--", color=PALETTE["accent"], linewidth=1.5,
            label="Ideal (y = ŷ)", zorder=3)
    ax.set_xlim(lims)
    ax.set_ylim(lims)

    # Linha de regressão ajustada
    m, b, *_ = stats.linregress(y_true, y_pred)
    x_line = np.array(lims)
    ax.plot(x_line, m * x_line + b, "-", color=PALETTE["primary"],
            linewidth=1.5, alpha=0.8, label=f"Regressão ajustada", zorder=4)

    ax.legend(fontsize=7.5, framealpha=0.7)
    cb = plt.colorbar(sc, ax=ax, pad=0.02)
    cb.set_label("|Resíduo|", fontsize=8)
    cb.ax.tick_params(labelsize=7)

    bbox = dict(boxstyle="round,pad=0.4", fc="white", ec="#AEB6BF", alpha=0.85)
    ax.text(0.04, 0.95,
            f"R²  = {metrics['R²']:.4f}\nMAE = {metrics['MAE']:.4f}",
            transform=ax.transAxes, fontsize=8.5,
            verticalalignment="top", bbox=bbox)

    setup_ax(ax, "Predito vs Real (conjunto de teste)",
             "Score Real (Heurístico)", "Score Predito pelo Modelo")


def plot_residuals_vs_predicted(ax, y_true, y_pred):
    """2. Resíduos vs Predito para checar padrões de erro."""
    residuals = y_true - y_pred

    sc = ax.scatter(
        y_pred, residuals,
        c=np.abs(residuals), cmap="coolwarm",
        alpha=0.50, s=16, edgecolors="none",
    )
    ax.axhline(0, color=PALETTE["accent"], linewidth=1.5, linestyle="--", zorder=3)

    # Banda de ±MAE
    mae = mean_absolute_error(y_true, y_pred)
    ax.axhline(mae, color=PALETTE["warn"], linewidth=1, linestyle=":",
               alpha=0.8, label=f"+MAE ({mae:.4f})")
    ax.axhline(-mae, color=PALETTE["warn"], linewidth=1, linestyle=":",
               alpha=0.8, label=f"−MAE")
    ax.legend(fontsize=7.5, framealpha=0.7)

    plt.colorbar(sc, ax=ax, pad=0.02).ax.tick_params(labelsize=7)
    setup_ax(ax, "Resíduos vs Predito",
             "Score Predito", "Resíduo (Real − Predito)")


def plot_residuals_distribution(ax, y_true, y_pred):
    """3. Histograma + KDE + curva normal dos resíduos."""
    residuals = y_true - y_pred
    mu, sigma = residuals.mean(), residuals.std()

    n_bins = 35
    ax.hist(residuals, bins=n_bins, density=True,
            color=PALETTE["light"], edgecolor="white",
            alpha=0.85, label="Histograma")

    # KDE empírica
    kde = stats.gaussian_kde(residuals)
    x_kde = np.linspace(residuals.min(), residuals.max(), 300)
    ax.plot(x_kde, kde(x_kde), color=PALETTE["primary"],
            linewidth=2, label="KDE empírica")

    # Distribuição normal teórica
    x_norm = np.linspace(residuals.min(), residuals.max(), 300)
    ax.plot(x_norm, stats.norm.pdf(x_norm, mu, sigma),
            "--", color=PALETTE["accent"], linewidth=1.8,
            label=f"Normal N({mu:.4f}, {sigma:.4f})")

    ax.axvline(0, color="#5D6D7E", linewidth=1, linestyle=":")
    ax.legend(fontsize=7.5, framealpha=0.7)

    bbox = dict(boxstyle="round,pad=0.4", fc="white", ec="#AEB6BF", alpha=0.85)
    ax.text(0.96, 0.96,
            f"μ = {mu:.5f}\nσ = {sigma:.5f}",
            transform=ax.transAxes, fontsize=8,
            verticalalignment="top", horizontalalignment="right", bbox=bbox)

    setup_ax(ax, "Distribuição dos Resíduos",
             "Resíduo (Real − Predito)", "Densidade")


def plot_qq(ax, y_true, y_pred):
    """4. Q-Q Plot dos resíduos para verificar normalidade."""
    residuals = y_true - y_pred
    (osm, osr), (slope, intercept, r) = stats.probplot(residuals, dist="norm")

    ax.scatter(osm, osr, color=PALETTE["primary"], alpha=0.5, s=14, edgecolors="none")

    x_line = np.array([osm[0], osm[-1]])
    ax.plot(x_line, slope * x_line + intercept,
            color=PALETTE["accent"], linewidth=1.8, linestyle="--",
            label=f"Linha Normal (r = {r:.4f})")

    ax.legend(fontsize=7.5, framealpha=0.7)
    setup_ax(ax, "Q-Q Plot dos Resíduos",
             "Quantis Teóricos (Normal)", "Quantis Observados")


def plot_feature_importance(ax, model, feature_names):
    """5. Importância das features (horizontal bar chart)."""
    importances = model.feature_importances_
    indices = np.argsort(importances)  # ascendente para plotar com barh

    colors = plt.cm.RdYlGn(importances[indices] / importances.max())

    bars = ax.barh(
        range(len(indices)),
        importances[indices],
        color=colors, edgecolor="white", height=0.7,
    )
    ax.set_yticks(range(len(indices)))
    ax.set_yticklabels([feature_names[i] for i in indices], fontsize=8)

    for bar, val in zip(bars, importances[indices]):
        ax.text(bar.get_width() + 0.002, bar.get_y() + bar.get_height() / 2,
                f"{val:.3f}", va="center", fontsize=7.5, color="#2C3E50")

    ax.set_xlim(0, importances.max() * 1.18)
    setup_ax(ax, "Importância das Features (Gini)",
             "Importância Média", "")


def plot_error_cdf(ax, y_true, y_pred, metrics_train, metrics_test):
    """6. CDF do erro absoluto + tabela de métricas."""
    abs_err = np.abs(y_true - y_pred)
    sorted_err = np.sort(abs_err)
    cdf = np.arange(1, len(sorted_err) + 1) / len(sorted_err)

    ax.plot(sorted_err, cdf * 100, color=PALETTE["primary"], linewidth=2)
    ax.fill_between(sorted_err, cdf * 100, alpha=0.12, color=PALETTE["primary"])

    for pct, ls, col in [(50, "--", PALETTE["success"]),
                          (90, "-.", PALETTE["warn"]),
                          (95, ":", PALETTE["accent"])]:
        val = np.percentile(abs_err, pct)
        ax.axvline(val, linestyle=ls, color=col, linewidth=1.4,
                   label=f"P{pct} = {val:.4f}")
        ax.axhline(pct, linestyle=ls, color=col, linewidth=0.8, alpha=0.4)

    ax.legend(fontsize=7.5, loc="lower right", framealpha=0.7)

    # Mini-tabela de métricas no canto superior esquerdo
    keys = ["MAE", "RMSE", "R²", "MAPE (%)"]
    lines = [f"{'Métrica':<14} {'Treino':>8} {'Teste':>8}",
             "─" * 32]
    for k in keys:
        lines.append(f"{k:<14} {metrics_train[k]:>8.4f} {metrics_test[k]:>8.4f}")
    table_text = "\n".join(lines)

    ax.text(0.02, 0.98, table_text,
            transform=ax.transAxes, fontsize=7.2,
            verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec="#AEB6BF", alpha=0.9))

    setup_ax(ax, "CDF do Erro Absoluto (teste)",
             "Erro Absoluto |Real − Predito|", "% das Predições")
    ax.set_ylim(0, 102)


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------

def main():
    print("Carregando pipeline de dados...")
    X_train, X_test, y_train, y_test, df_test, feature_names = load_and_prepare()

    print("Carregando modelo...")
    model = joblib.load(MODEL_PATH)

    print("Calculando predições...")
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    metrics_train = calculate_metrics(y_train, y_pred_train, "Treino")
    metrics_test = calculate_metrics(y_test, y_pred_test, "Teste")
    print_metrics(metrics_train, metrics_test)

    print("\nGerando figura de avaliação...")
    fig = plt.figure(figsize=(18, 11))
    fig.patch.set_facecolor(PALETTE["bg"])

    fig.suptitle(
        "Avaliação do Modelo Random Forest — Risco de Ataque de Tubarão",
        fontsize=15, fontweight="bold", color="#1B2631", y=0.98,
    )

    gs = gridspec.GridSpec(
        2, 3, figure=fig,
        hspace=0.42, wspace=0.34,
        left=0.06, right=0.97, top=0.93, bottom=0.07,
    )

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])
    ax4 = fig.add_subplot(gs[1, 0])
    ax5 = fig.add_subplot(gs[1, 1])
    ax6 = fig.add_subplot(gs[1, 2])

    plot_predicted_vs_actual(ax1, y_test, y_pred_test, metrics_test)
    plot_residuals_vs_predicted(ax2, y_test, y_pred_test)
    plot_residuals_distribution(ax3, y_test, y_pred_test)
    plot_qq(ax4, y_test, y_pred_test)
    plot_feature_importance(ax5, model, feature_names)
    plot_error_cdf(ax6, y_test, y_pred_test, metrics_train, metrics_test)

    fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight",
                facecolor=PALETTE["bg"])
    print(f"\nFigura salva em: {OUTPUT_PATH}")
    plt.show()


if __name__ == "__main__":
    main()
