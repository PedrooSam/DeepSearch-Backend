import os
import sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import joblib
import mlflow
import mlflow.sklearn

from sklearn.ensemble import RandomForestRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import (
    train_test_split, RandomizedSearchCV, KFold
)
from sklearn.metrics import mean_absolute_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "projeto", "dados"))
if DADOS_DIR not in sys.path:
    sys.path.insert(0, DADOS_DIR)

from heuristicas import extract_features, compute_heuristic_score, DATASET_PATH

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

    return X, y


def train_and_log(experiment_name, run_name, model_class, param_dist,
                  X_train, X_test, y_train, y_test,
                  n_iter=20, model_kwargs=None):
    """
    Treina um modelo com RandomSearch + K-Fold no treino,
    avalia no holdout e registra tudo no MLflow.
    """
    if model_kwargs is None:
        model_kwargs = {}

    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=run_name):

        # RandomSearch com K-Fold sobre o conjunto de treino
        kfold = KFold(n_splits=5, shuffle=True, random_state=42)
        search = RandomizedSearchCV(
            estimator=model_class(random_state=42, **model_kwargs),
            param_distributions=param_dist,
            n_iter=n_iter,
            cv=kfold,
            scoring="r2",
            random_state=42,
            n_jobs=-1,
        )
        search.fit(X_train, y_train)

        # Log dos melhores parâmetros encontrados
        mlflow.log_params(search.best_params_)
        mlflow.log_metric("cv_r2_mean", search.best_score_)
        cv_r2_std = search.cv_results_["std_test_score"][search.best_index_]
        mlflow.log_metric("cv_r2_std", cv_r2_std)

        # Avaliação final no holdout
        best_model = search.best_estimator_
        y_pred = best_model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        mlflow.log_metric("test_MAE", mae)
        mlflow.log_metric("test_R2", r2)
        mlflow.sklearn.log_model(best_model, artifact_path="model")

        print(f"  CV R²={search.best_score_:.4f} ± {cv_r2_std:.4f} | "
              f"Holdout MAE={mae:.4f} | Holdout R²={r2:.4f}")
        print(f"  Melhores parâmetros: {search.best_params_}")

    return best_model


def main():
    mlflow.set_tracking_uri(MLFLOW_URI)

    print("Carregando dados...")
    X, y = load_data()

    # Holdout: separa 20% como conjunto de teste final
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    print(f"  Treino: {len(X_train)} amostras | Holdout: {len(X_test)} amostras\n")

    # ------------------------------------------------------------------
    # Experimento 1: Random Forest
    # RandomSearch testa 20 combinações de hiperparâmetros via K-Fold (5 folds)
    # ------------------------------------------------------------------
    print("=== Experimento 1: Random Forest ===")
    rf_param_dist = {
        "n_estimators": [100, 150, 200, 300],
        "max_depth": [8, 10, 12, 15, None],
        "min_samples_leaf": [1, 2, 3, 5],
        "max_features": ["sqrt", "log2"],
    }
    best_rf = train_and_log(
        experiment_name="SharkRisk - Random Forest",
        run_name="random_forest_randomsearch",
        model_class=RandomForestRegressor,
        param_dist=rf_param_dist,
        X_train=X_train, X_test=X_test,
        y_train=y_train, y_test=y_test,
        n_iter=20,
        model_kwargs={"n_jobs": -1},
    )

    # Persiste o melhor RF como modelo de produção
    joblib.dump(best_rf, os.path.join(DADOS_DIR, "modelo_risco.pkl"))
    print("  Modelo de produção salvo.\n")

    # ------------------------------------------------------------------
    # Experimento 2: Decision Tree (modelo de comparação)
    # Mesmo pipeline: RandomSearch + K-Fold + holdout
    # ------------------------------------------------------------------
    print("=== Experimento 2: Decision Tree ===")
    dt_param_dist = {
        "max_depth": [3, 5, 8, 10, 12, 15, None],
        "min_samples_leaf": [1, 2, 3, 5, 10],
        "min_samples_split": [2, 5, 10],
        "max_features": ["sqrt", "log2", None],
    }
    train_and_log(
        experiment_name="SharkRisk - Decision Tree",
        run_name="decision_tree_randomsearch",
        model_class=DecisionTreeRegressor,
        param_dist=dt_param_dist,
        X_train=X_train, X_test=X_test,
        y_train=y_train, y_test=y_test,
        n_iter=20,
    )

    print("\nTreinamento concluído! Acesse o MLflow em: http://localhost:5000")


if __name__ == "__main__":
    main()
