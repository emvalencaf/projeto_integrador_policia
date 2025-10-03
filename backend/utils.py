from pathlib import Path
import pickle
from statsforecast import StatsForecast
import pandas as pd


def load_models(models_path: Path):
    models = {}
    for model_dir in models_path.iterdir():
        if model_dir.is_dir():
            dir_name = model_dir.name
            models[dir_name] = {}
            print(models)
            for model_file in model_dir.iterdir():
                if not model_file.is_file() and model_file.suffix != ".pkl":
                    continue
                model_name = model_file.name.split("_")[0]
                with open(model_file, "rb") as f:
                    models[dir_name][model_name] = pickle.load(f)
    print("Loaded all machine learning models")
    return models

def load_csv(dfs_path: Path):
    dfs = {}
    for output_dir in dfs_path.iterdir():
        dir_name = output_dir.name
        print(dir_name)
        for csv_file in output_dir.iterdir():
            if not csv_file.is_file() and csv_file.suffix != ".csv":
                continue
            df = pd.read_csv(csv_file)
            df["data_ocorrencia"] = pd.to_datetime(df["data_ocorrencia"])
            
            dfs[dir_name] = df
    return dfs