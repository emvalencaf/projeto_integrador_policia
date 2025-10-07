# Projeto Integrador: Análise Preditiva de Crimes

Sistema de análise preditiva para identificação de hotspots criminais e previsão temporal de ocorrências, desenvolvido para apoio à tomada de decisão da Polícia Civil de Pernambuco.

## Equipe

- Augusto
- Denilson
- Edson
- Hugo
- Jonathan
- Vilton

## Visão Geral do Projeto

O sistema é composto por três módulos que trabalham de forma integrada:

1. **Módulo ML**: Realiza o treinamento dos modelos de machine learning para identificar hotspots criminais e prever a quantidade de ocorrências futuras
2. **Módulo Backend**: Disponibiliza uma API REST para consumo das previsões geradas pelos modelos treinados
3. **Módulo Frontend**: Disponibiliza uma interface dashboard para visualizar de forma iterativa.

## Estrutura do Projeto

```
projeto_integrador_policia/
│
├── frontend/                  
│   ├── app.py                # Arquivo principal
│   ├── config.py             # Configuração do ambiente
│   ├── utils.py              # Funções auxiliares (carregamento de modelos/dados)
│   └── requirements.txt      # Dependências do backend
│
├── backend/                  # API REST (FastAPI)
│   ├── main.py               # Aplicação principal com endpoints
│   ├── pipeline.py           # Pipeline de previsão
│   ├── utils.py              # Funções auxiliares (carregamento de modelos/dados)
│   ├── dependencies.py       # Gerenciamento de dependências da API
│   └── requirements.txt      # Dependências do backend
│
├── ml/                  
│   ├── notebooks/                  # Notebooks Jupyter
│   │   ├── ml_train.ipynb          # Treinamento dos modelos
│   │   ├── prepare_dataset.ipynb   # Preparação dos datasets
│   │   └── preview.ipynb           # Visualização dos resultados
│   │
│   ├── models/                  # Modelos treinados (.pkl)
│   │   └── chicago/             # 135 modelos (um para cada hotspot)
│   │
│   ├── output/               # Dados processados
│   │   └── chicago/
│   │       └── violent_crimes_chicago.csv
│   │
│   └── requirements.txt      # Dependências do ML
│
└── README.md    
```

## Módulo ML (Machine Learning)

### Pipeline de Treinamento

O módulo ML implementa um pipeline completo de análise espacial e previsão temporal:

#### 1. Identificação de Hotspots (HDBSCAN)
- Utiliza o algoritmo **HDBSCAN** para clustering espacial de crimes
- Identifica automaticamente áreas de alta concentração criminal (hotspots)
- Parâmetros configuráveis:
  - `min_cluster_size`: 200 (tamanho mínimo do cluster)
  - `min_samples`: 60 (amostras mínimas)
  - `metric`: haversine (métrica para coordenadas geográficas)

#### 2. Previsão Temporal (AutoARIMA)
- Treina um modelo **AutoARIMA** individual para cada hotspot identificado
- Realiza previsões de séries temporais com sazonalidade semanal (7 dias)
- Avalia performance com métricas MAE e RMSE
- Armazena histórico de experimentos usando MLflow

### Notebooks Disponíveis

#### `ml_train.ipynb`
Notebook principal de treinamento que executa:
1. Carregamento do dataset de crimes
2. Aplicação do HDBSCAN para identificar hotspots espaciais
3. Criação de séries temporais por hotspot (agregação diária)
4. Treinamento de modelo AutoARIMA para cada hotspot
5. Avaliação com split treino/teste (80/20)
6. Salvamento dos modelos em formato pickle
7. Registro de métricas e artefatos no MLflow

#### `prepare_dataset.ipynb`
Preparação e padronização de datasets de diferentes cidades para formato comum.

#### `preview.ipynb`
Visualização e análise dos resultados dos modelos treinados.

### Artefatos Gerados

- **Modelos**: Arquivos `.pkl` em `ml/models/chicago/` (um modelo StatsForecast por hotspot)
- **Dados processados**: CSV com crimes etiquetados por hotspot em `ml/output/chicago/`
- **Experimentos MLflow**: Rastreamento de métricas, parâmetros e artefatos em `ml/mlops/`

### Tecnologias Utilizadas

- **HDBSCAN**: Clustering espacial baseado em densidade
- **StatsForecast**: Biblioteca para previsão de séries temporais
- **AutoARIMA**: Modelo automático de séries temporais com busca de hiperparâmetros
- **MLflow**: Rastreamento de experimentos e versionamento de modelos
- **Pandas/NumPy**: Manipulação e processamento de dados

## Módulo Backend (API)

### Descrição

API REST desenvolvida em **FastAPI** que disponibiliza endpoints para consumo das previsões de crimes por hotspot.

### Endpoints Disponíveis

#### `POST /forecast`
Retorna previsão para um hotspot específico.

**Request Body:**
```json
{
  "city": "chicago",
  "days": 7
}
```

**Parâmetros:**
- `city`: Cidade dos dados (ex: "chicago")
- `days`: Número de dias a prever (padrão: 7)

**Response:** Array com previsões diárias contendo:
- `ds`: Data da previsão
- `min_crimes`: Valor mínimo previsto de ocorrências
- `mean_crimes`: Valor médio previsto de ocorrências
- `max_crimes`: Valor máximo previsto de ocorrências
- `latitude`: Coordenada do centroide do hotspot
- `longitude`: Coordenada do centroide do hotspot
- `hotspot_id`: Identificador do hotspot

### Arquitetura da API

- **main.py**: Definição dos endpoints e aplicação FastAPI
- **pipeline.py**: Lógica de geração de previsões
- **utils.py**: Carregamento de modelos e datasets
- **dependencies.py**: Injeção de dependências (modelos e dados)
- **CORS**: Configurado para permitir requisições de qualquer origem

### Tecnologias Utilizadas

- **FastAPI**: Framework web moderno e de alta performance
- **Pydantic**: Validação de dados e serialização
- **Uvicorn**: Servidor ASGI para rodar a aplicação

## Como Rodar o Projeto

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### 1. Módulo de Machine Learning (`/ml`)

Execute estes comandos no terminal:

```bash
# Navegar para o diretório ML
cd ml

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar notebooks
jupyter notebook
```

**Ordem recomendada de execução:**
1. `prepare_dataset.ipynb` - Preparar os dados
2. `ml_train.ipynb` - Treinar os modelos
3. `preview.ipynb` - Visualizar resultados

### 2. Módulo Backend (`/backend`)

Execute estes comandos no terminal:

```bash
# Navegar para o diretório backend
cd backend

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Executar a API
uvicorn main:app --reload
```

A API estará disponível em: `http://localhost:8000`

Documentação interativa (Swagger): `http://localhost:8000/docs`

## Fluxo de Trabalho Completo

1. **Preparação dos dados**: Execute `prepare_dataset.ipynb` para padronizar os dados de entrada
2. **Treinamento**: Execute `ml_train.ipynb` para gerar os hotspots e treinar os modelos
3. **Validação**: Use `preview.ipynb` para visualizar e validar os resultados
4. **Deploy**: Inicie a API com `uvicorn` para disponibilizar as previsões
5. **Consumo**: Faça requisições aos endpoints para obter previsões

## Dados de Entrada

O sistema espera arquivos CSV com as seguintes colunas:
- `data_ocorrencia`: Data da ocorrência (formato date)
- `latitude`: Coordenada geográfica
- `longitude`: Coordenada geográfica
- `tipo_crime`: Tipo de crime (opcional, para filtragem)

## Como rodar

### Módulo de Machine Learning (`/ml`)

- Abra o terminal e digite `cd ml`
- Crie um ambiente python à nível de projeto `python -m venv venv`.
- Ative o ambiente python à nível de projeto com os seguintes comandos:
    - Para o windows: `venv/Scripts/activate`
    - Para o linux: `source venv/bin/activate`
- Instale as dependências com o comando `pip install -r requirements.txt`

