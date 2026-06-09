# DeepSearch — Predição de Risco de Ataque de Tubarão

> **Disciplina:** Machine Learning e Projeto 6
> **Instituição:** CESAR School
> **Período:** 2026.1

## Membros do grupo

<!-- Preencher com nomes e usuários GitHub -->
| Nome | GitHub |
|------|--------|
| Felipe França | [FelipeARFranca](https://github.com/FelipeARFranca) |
| Felipe Matias | [Zibec](https://github.com/Zibec) |
| Gabriel Landim | [GabrielQlandim](https://github.com/Gabrielqlandim) |
| Luis Gustavo | [Luis-Gustavo-Melo](https://github.com/Luis-Gustavo-Melo) |
| Pedro Sampaio | [PedrooSam](https://github.com/PedrooSam) |
| Manuela Cavalcanti | [FelipeARFranca](https://github.com/FelipeARFranca) |
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
│       ├── heuristicas.py    # Pipeline de features e score heurístico
│       ├── avaliacao_modelo.py  # Avaliação visual do modelo (6 gráficos)
│       ├── dataset_tratado_final.csv
│       └── modelo_risco.pkl  # Modelo treinado (gerado pelo train.py)
├── frontend/                 # Frontend Next.js — mapa interativo
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

O script treina 2 modelos em 2 experimentos separados e registra tudo no MLflow:

| Experimento | Modelo | Busca de hiperparâmetros |
|-------------|--------|--------------------------|
| SharkRisk - Random Forest | Random Forest | RandomizedSearchCV |
| SharkRisk - Decision Tree | Decision Tree | RandomizedSearchCV |

Acesse http://localhost:5000 para comparar os experimentos, métricas e modelos salvos.

### 3. Gerar avaliação visual do modelo

```bash
python projeto/dados/avaliacao_modelo.py
```

Gera `projeto/dados/avaliacao_modelo.png` com 6 gráficos: Predito vs Real, Resíduos vs Predito, Distribuição dos Resíduos, Q-Q Plot, Importância das Features e CDF do Erro Absoluto.

### 4. Parar os containers

```bash
docker compose down
```

## Modelos treinados

| Modelo | Estratégia de busca | Validação |
|--------|--------------------|-----------| 
| Random Forest | RandomizedSearchCV (20 iter) | Holdout 80/20 + CV 5-fold |
| Decision Tree | RandomizedSearchCV (20 iter) | Holdout 80/20 + CV 5-fold |

## Métricas registradas no MLflow

- `cv_r2_mean` — R² médio da validação cruzada 5-fold (sobre o treino)
- `test_MAE` — Mean Absolute Error no holdout
- `test_R2` — R² no holdout

## Métricas adicionais (avaliacao_modelo.py)

Calculadas sobre treino e teste e exibidas nos gráficos:

- MAE, MSE, RMSE, R², MAPE, Explained Variance Score
