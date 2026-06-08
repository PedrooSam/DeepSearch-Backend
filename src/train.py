import os
import sys
import warnings
warnings.filterwarnings("ignore")

import mlflow
import mlflow.sklearn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "projeto", "dados"))
if DADOS_DIR not in sys.path:
    sys.path.insert(0, DADOS_DIR)

from heuristicas import train

MLFLOW_URI = os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlruns/mlflow.db")


def main():
    mlflow.set_tracking_uri(MLFLOW_URI)
    mlflow.set_experiment("SharkRisk - Random Forest")

    with mlflow.start_run(run_name="random_forest_baseline"):

        # Parâmetros do modelo (os mesmos que já estavam em heuristicas.py)
        params = {
            "n_estimators": 200,
            "max_depth": 12,
            "min_samples_leaf": 3,
            "test_size": 0.2,
            "random_state": 42,
        }
        mlflow.log_params(params)

        # Treina usando a função que já existe
        model, _, metrics = train()

        # Registra as métricas no MLflow
        mlflow.log_metric("MAE", metrics["MAE"])
        mlflow.log_metric("R2", metrics["R2"])

        # Salva o modelo no MLflow
        mlflow.sklearn.log_model(model, artifact_path="model")

        print("Experimento registrado no MLflow!")
        print(f"Acesse: {MLFLOW_URI}")


if __name__ == "__main__":
    main()
