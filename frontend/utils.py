import json
import pandas as pd

def process_predictions(data: dict):
    """Converte JSON de previsões para DataFrame"""
    if isinstance(data, str):
        dados = json.loads(data)
    
    if 'forecast' in data:
        forecast = data.get('forecast')
        if not forecast:
            raise ValueError("Formato inesperado para 'forecast'")
        df = pd.DataFrame(forecast)
        df['ds'] = pd.to_datetime(df['ds'])
        return df
    else:
        return pd.DataFrame(data)