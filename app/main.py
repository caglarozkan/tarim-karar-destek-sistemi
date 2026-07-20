from fastapi import FastAPI
import models
from database import engine
import routes


models.Base.metadata.create_all(bind=engine)
# Uygulamayı başlatıyoruz
app = FastAPI(
    title="Tarımsal Karar ve Risk Analiz Sistemi",
    description="Çiftçiler için risk analizi ve arazi optimizasyonu sağlayan backend servisi.",
    version="1.0.0"
)

# Ana sayfa (Root) uç noktası
@app.get("/")
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Bütün GET, POST işlemlerine izin ver
    allow_headers=["*"], # Bütün veri başlıklarına izin ver
)

app.include_router(routes.router)