import pandas as pd

def pipeline_forecast(days: int, hotspot_id: float, df: pd.DataFrame, model):
    ts = df.groupby("data_ocorrencia").size().reset_index(name="y")
    ts["unique_id"] = str(0.0)
    ts = ts.rename(columns={"data_ocorrencia": "ds"})
    # Faz forecast
    fcst = model.forecast(df=ts.head(1000), h=days, level=[95])
    
    # Adiciona latitude/longitude do hotspot (centroide)
    lat = df["latitude"].mean()
    lon = df["longitude"].mean()
    
    fcst["latitude"] = lat
    fcst["longitude"] = lon
    fcst["hotspot_id"] = hotspot_id
    
    return fcst