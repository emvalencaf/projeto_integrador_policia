from io import BytesIO
from typing import Annotated
from fastapi import Depends, FastAPI, Form, HTTPException, UploadFile, File
from pipeline import pipeline_crime_hotspot
from dependencies import get_models
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Crime Hotspot API",
    description="API para previsão de hotspots de crimes",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
    
@app.post("/forecast")
async def forecast(
    city: Annotated[str, Form(...)],
    days: Annotated[int, Form(...)],
    file: Annotated[UploadFile, File(...)],
    models=Depends(get_models),
):
    city_models = models.get(city.lower(), None)
    
    if not city_models:
        raise HTTPException(status_code=400, detail=f"Não há modelos treinados para a cidade: {city}")
    
    if file is None:
        raise HTTPException(status_code=400, detail="Envie um arquivo .csv ou .xlsx")
    
    if file.filename is None:
        raise HTTPException(status_code=400, detail="Envie um arquivo .csv ou .xlsx")
    
    filename = file.filename.lower()
    
    suffix = filename.split(".")[-1]
    
    if not suffix in ["csv", "xlsx"]:
        raise HTTPException(status_code=400, detail="Envie um arquivo .csv ou .xlsx")

    content = await file.read()
    
    bytes_io = BytesIO(content)
    
    try:
        df = pd.read_csv(bytes_io) if suffix == "csv" else pd.read_excel(bytes_io)
    except Exception as e:
        raise HTTPException(status_code=400, detail="Erro ao ler o arquivo. Verifique o formato e o conteúdo.")
    
    if "latitude" not in df.columns or "longitude" not in df.columns or "data_ocorrencia" not in df.columns:
        raise HTTPException(status_code=400, detail="O arquivo deve conter as colunas: latitude, longitude, data_ocorrencia")
    
    df["data_ocorrencia"] = pd.to_datetime(df["data_ocorrencia"], errors='coerce')
    
    if df["data_ocorrencia"].isnull().all():
        raise HTTPException(status_code=400, detail="A coluna 'data_ocorrencia' deve conter datas válidas.")
    try:
        forecast = pipeline_crime_hotspot(df=df, days=days, models=city_models)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a previsão: {str(e)}")
    
    return {"forecast": forecast}