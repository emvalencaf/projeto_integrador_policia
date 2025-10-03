from pathlib import Path
from utils import load_csv, load_models

models_path = Path("../ml/models")
dfs_path = Path("../ml/output")

models = load_models(models_path=models_path)
dfs = load_csv(dfs_path=dfs_path)

def get_models():
    return models

def get_dfs():
    return dfs
