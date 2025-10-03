from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from dependencies import get_dfs, get_models
from pipeline import pipeline_forecast
import pandas as pd

app = FastAPI(
    title="Crime Hotspot API",
    description="API para previsão de hotspots de crimes",
    version="1.0.0"
)

class ForecastRequest(BaseModel):
    hotspot_id: float
    city: str
    horizon: int = 7  # número de dias a prever

class ForecastAll(BaseModel):
    city: str
    horizon: int = 7

@app.post("/forecast")
def forecast(request: ForecastRequest,
             models=Depends(get_models),
             dfs=Depends(get_dfs)):
    df = dfs.get(request.city, None)
    hotspot_data = df[df["hotspot_id"] == float(request.hotspot_id)].copy()

    models_city = models.get(request.city)
    model = models_city.get(str(request.hotspot_id))
    forecast = pipeline_forecast(days=request.horizon,
                      df=hotspot_data,
                      hotspot_id=request.hotspot_id,
                      model=model)
    
    return forecast.to_dict(orient="records")

@app.post("/forecast_all")
def forecast_all(request: ForecastAll,
                 models=Depends(get_models),
                 dfs=Depends(get_dfs)):
    df = dfs.get(request.city)
    
    models_city = models.get(request.city)
    
    all = []
    for hotspot_id, model in models_city.items():
        print("predicting... ", hotspot_id)
        hotspot_data = df[df["hotspot_id"] == float(hotspot_id)].copy()
        forecast = pipeline_forecast(days=request.horizon,
                      df=hotspot_data,
                      hotspot_id=hotspot_id,
                      model=model)
        all.append(forecast)
    
    forecast_map = pd.concat(all, ignore_index=True)
    
    return forecast_map.to_dict(orient="records")