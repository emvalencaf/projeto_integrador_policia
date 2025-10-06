from pathlib import Path
import pickle
from statsforecast import StatsForecast

def load_models(models_path: Path):
    models = {}
    for model_dir in models_path.iterdir():
        if model_dir.is_dir():
            dir_name = model_dir.name
            models[dir_name] = {}
            for model_file in model_dir.iterdir():
                if not model_file.is_file() and model_file.suffix != ".pkl":
                    continue
                filename = model_file.name.lower().split(".")[0]
                model_name = filename.split("_")[0]
                with open(model_file, "rb") as f:
                    models[dir_name][model_name] = pickle.load(f)
    print("Loaded all machine learning models")
    return models