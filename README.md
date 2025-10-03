# Projeto Integrador: 

Repositório principal para o projeto inegrador

## Equipe

- Augusto
- Denilson
- Edson
- Hugo
- Jonathan
- Vilton

## Estrutura do Projeto
```
|__ backend
|__ frontend
|__ ml
```

- `backend`: diretório em que será concentrado todo o código para a API
- `ml`: diretório em que será concentrado todo o código para o treinamento dos modelos de machine learning e os artefatos criados.
- `frontend`: diretório em que será concentrado todo o código para o frontend.

### Módulo ML

O notebook `ml_train.ipynb` serve para treinar os modelos:
- Nele é aplicada a técnica do DBHSCAN para achar os hotspot nos dados espaciais.
- Em seguida é treinado um modelo SARIMA para cada hotspot.

O notebook `prepare_dataset.ipynb` serve para preparar dados de crimes para uma formatação comum:

O notebook `preview.ipynb` serve para renderizar os modelos.

## Como rodar

### Módulo de Machine Learning (`/ml`)

- Abra o terminal e digite `cd ml`
- Crie um ambiente python à nível de projeto `python -m venv venv`.
- Ative o ambiente python à nível de projeto com os seguintes comandos:
    - Para o windows: `venv/Scripts/activate`
    - Para o linux: `source venv/bin/activate`
- Instale as dependências com o comando `pip install -r requirements.txt`

