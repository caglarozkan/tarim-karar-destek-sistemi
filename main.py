from fastapi import FastAPI

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