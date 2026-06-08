# DeepSearch — Predição de Risco de Ataque de Tubarão

> **Disciplina:** Machine Learning I e Projeto 3
> **Instituição:** CESAR School
> **Período:** 2026.1

## Membros do grupo

<!-- Preencher com nomes e usuários GitHub -->
| Nome | GitHub |
|------|--------|
| A preencher | @usuario |

## Sobre a solução

<!-- Adicionar link do Google Sites quando disponível -->

O DeepSearch é uma solução completa de Machine Learning para predição de risco de ataques de tubarão em praias. O sistema combina dados ambientais (temperatura do mar, maré, clima, horário) com o histórico de incidentes para calcular, em tempo real, um score de risco entre 0 e 1.

A solução é composta por:
- **Backend Django** — API REST com endpoint de predição
- **Frontend Next.js** — Mapa interativo de risco com Leaflet
- **MLflow** — Rastreamento de experimentos e versionamento de modelos
- **Docker** — Ambiente containerizado e reprodutível

## Estrutura do repositório

```
/
├── data/                     # Dados brutos e processados
├── notebooks/                # EDA e experimentos
├── src/
│   └── train.py              # Script de treinamento com MLflow
├── projeto/                  # Backend Django
│   ├── apps/
│   │   ├── beaches/          # Gerenciamento de praias
│   │   ├── forecasts/        # Dados de previsão
│   │   ├── incidents/        # Registro de incidentes
│   │   ├── ml/               # Endpoint de predição
│   │   └── risk/             # Avaliação de risco
│   └── dados/
│       ├── heuristicas.py    # Pipeline de features e treinamento
│       ├── avaliacao_modelo.py
│       └── modelo_risco.pkl  # Modelo treinado
├── frontend/                 # Frontend Next.js
├── mlruns/                   # Experimentos MLflow (gerado automaticamente)
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Como executar

### Pré-requisitos

- [Docker](https://www.docker.com/products/docker-desktop) instalado e rodando

### 1. Subir os containers

```bash
docker compose up --build
```

Após o build, os serviços ficam disponíveis em:

| Serviço | URL |
|---------|-----|
| Backend (API) | http://localhost:8000 |
| Frontend | http://localhost:3000 |
| MLflow | http://localhost:5000 |
| Swagger (docs) | http://localhost:8000/docs |

### 2. Treinar os modelos com MLflow

Com os containers rodando, execute em outro terminal:

```bash
pip install mlflow matplotlib scikit-learn pandas joblib
python src/train.py
```

O script treina 4 modelos em 2 experimentos e registra tudo no MLflow:

| Experimento | Modelos |
|-------------|---------|
| SharkRisk - Modelos Base | Decision Tree (GridSearchCV), KNN |
| SharkRisk - Modelos Ensemble | Random Forest (RandomizedSearchCV), AdaBoost |

Acesse http://localhost:5000 para comparar os experimentos, métricas e modelos salvos.

### 3. Parar os containers

```bash
docker compose down
```

## Modelos treinados

| Modelo | Estratégia de busca | Validação |
|--------|--------------------|-----------| 
| Decision Tree | GridSearchCV | Holdout + CV 5-fold |
| KNN | Parâmetros fixos | Holdout + CV 5-fold |
| Random Forest | RandomizedSearchCV | Holdout + CV 5-fold |
| AdaBoost | Parâmetros fixos | Holdout + CV 5-fold |

## Métricas registradas no MLflow

- MAE, MSE, RMSE, R², MAPE, Explained Variance Score
- Cross-validation R² médio e desvio padrão (5-fold)
