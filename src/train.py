import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import mlflow
import mlflow.sklearn
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "projeto", "dados"))
if DADOS_DIR not in sys.path:
    sys.path.insert(0, DADOS_DIR)

from heuristicas import train, extract_features, compute_heuristic_score, DATASET_PATH

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlruns/mlflow.db")


def load_data():
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
    y = df["risk_score"].values

    return train_test_split(X, y, test_size=0.2, random_state=42)


def main():
    mlflow.set_tracking_uri(MLFLOW_URI)

    # ------------------------------------------------------------------
    # Experimento 1: Random Forest
    # ------------------------------------------------------------------
    mlflow.set_experiment("SharkRisk - Random Forest")

    with mlflow.start_run(run_name="random_forest_baseline"):
        params = {
            "n_estimators": 200,
            "max_depth": 12,
            "min_samples_leaf": 3,
            "test_size": 0.2,
            "random_state": 42,
        }
        mlflow.log_params(params)

        model, _, metrics = train()

        mlflow.log_metric("MAE", metrics["MAE"])
        mlflow.log_metric("R2", metrics["R2"])
        mlflow.sklearn.log_model(model, artifact_path="model")

        print(f"[Random Forest] MAE={metrics['MAE']:.4f} | R²={metrics['R2']:.4f}")

    # ------------------------------------------------------------------
    # Experimento 2: Árvore de Decisão (modelo de comparação)
    # ------------------------------------------------------------------
    mlflow.set_experiment("SharkRisk - Decision Tree")

    with mlflow.start_run(run_name="decision_tree_baseline"):
        params = {
            "max_depth": 12,
            "min_samples_leaf": 3,
            "test_size": 0.2,
            "random_state": 42,
        }
        mlflow.log_params(params)

        X_train, X_test, y_train, y_test = load_data()

        dt = DecisionTreeRegressor(
            max_depth=params["max_depth"],
            min_samples_leaf=params["min_samples_leaf"],
            random_state=params["random_state"],
        )
        dt.fit(X_train, y_train)

        y_pred = dt.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        mlflow.log_metric("MAE", mae)
        mlflow.log_metric("R2", r2)
        mlflow.sklearn.log_model(dt, artifact_path="model")

        print(f"[Decision Tree]  MAE={mae:.4f} | R²={r2:.4f}")

    print(f"\nExperimentos registrados! Acesse: http://localhost:5000")


if __name__ == "__main__":
    main()
