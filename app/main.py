from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import engine
import app.routes

models.Base.metadata.create_all(bind=engine)

app_tarim = FastAPI(
    title="Tarımsal Karar ve Risk Analiz Sistemi",
    description="Çiftçiler için risk analizi ve arazi optimizasyonu sağlayan backend servisi.",
    version="1.0.0",
)

@app_tarim.get("/")
def baslangic():
    return {
        "mesaj": "Backend API sorunsuz çalışıyor!",
        "proje": "Yapay Zeka Destekli Tarımsal Karar ve Risk Analiz Sistemi",
        "durum": "Aktif",
    }

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:5174",
    "http://localhost:5179",
    "http://127.0.0.1:5179",
]

app_tarim.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app_tarim.include_router(app.routes.router)