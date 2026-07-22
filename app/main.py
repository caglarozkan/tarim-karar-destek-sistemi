from fastapi import FastAPI
from app import models
from app.database import engine
import app.routes


app.models.Base.metadata.create_all(bind=engine)
# Uygulamayı başlatıyoruz
app_tarim = FastAPI(
    title="Tarımsal Karar ve Risk Analiz Sistemi",
    description="Çiftçiler için risk analizi ve arazi optimizasyonu sağlayan backend servisi.",
    version="1.0.0"
)

# Ana sayfa (Root) uç noktası
@app_tarim.get("/")
def baslangic():
    return {
        "mesaj": "Backend API sorunsuz çalışıyor!",
        "proje": "Yapay Zeka Destekli Tarımsal Karar ve Risk Analiz Sistemi",
        "durum": "Aktif"
    }

from fastapi.middleware.cors import CORSMiddleware

# Arayüzün çalıştığı portlara geçiş izni veriyoruz
origins = [
    "http://localhost:5173",
    "http://localhost:3000",

]

app_tarim.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Bütün GET, POST işlemlerine izin ver
    allow_headers=["*"], # Bütün veri başlıklarına izin ver
)

app_tarim.include_router(app.routes.router)