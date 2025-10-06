from pathlib import Path
from utils import load_models

models_path = Path("../ml/models")

models = load_models(models_path=models_path)

def get_models():
    return models