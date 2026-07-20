#Risk analizi hesaplamalarını içeren modül.
import statistics
import pandas as pd
from pathlib import Path

# CSV dosyasının yolu
CSV_PATH = Path(__file__).resolve().parent / "data" / "processed" / "data_files" / "final_price_dataset.csv"

URUN_ESLESTIRME = {
    "BIBER SIVRI": "Biber (Sivri)",
    "DOMATES SALKIM": "Domates (Sofralık)",
    "KABAK TAZE": "Kabak (Sakız)",
    "PATLICAN UZUN": "Patlıcan",
    "SALATALIK SILOR": "Hıyar (Sofralık)",
    "SOGAN KURU": "Soğan (Kuru)",
    "KARPUZ": "Karpuz",
}


def fiyat_haritasi_olustur() -> dict[str, list[float]]:
    #ürün ve fiyatları
    df = pd.read_csv(CSV_PATH)
    harita = {}
    for csv_adi, sistem_adi in URUN_ESLESTIRME.items():
        fiyatlar = df[df["product_name"] == csv_adi]["average_price"].tolist()
        if fiyatlar:
            harita[sistem_adi] = fiyatlar
    print(harita)
    return harita

FIYAT_HARITASI = fiyat_haritasi_olustur()


def kota_doluluk_hesapla(kullanilan_kota: float, girilen_donum: float, maksimum_kota: float) -> float:
    #anlık kota güncellemesi yapar hesaplama için
    yeni_kota = kullanilan_kota + girilen_donum
    if maksimum_kota <= 0:
        return 0.0
    return (yeni_kota / maksimum_kota) * 100


def cv_hesapla(fiyatlar: list[float]) -> tuple[float, float, float]:
    """
    CV = (Standart Sapma / Ortalama) * 100
    Dönen değer: (cv, ortalama, standart_sapma)
    """
    ortalama = statistics.mean(fiyatlar)
    std = statistics.stdev(fiyatlar)
    if ortalama == 0:
        return 0.0, ortalama, std
    cv = (std / ortalama) * 100
    return cv, ortalama, std


def genel_risk_hesapla(kota_doluluk: float, cv: float) -> float:
    return 0.80 * kota_doluluk + 0.20 * cv


def risk_seviyesi_belirle(risk: float) -> tuple[str, str]:
    if risk <= 25:
        return "Güvenli", "🟢"
    elif risk <= 50:
        return "Orta Risk", "🟡"
    elif risk <= 75:
        return "Riskli", "🟠"
    else:
        return "Çok Riskli", "🔴"