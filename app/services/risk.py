"""
risk.py
Risk analizi hesaplama modülü.
AHP (Analytic Hierarchy Process) ile belirlenmiş ağırlıklara göre
5 faktörden oluşan bileşik bir risk skoru üretir:
Kota (0.38), Fiyat (0.29), Gübre (0.16), Mazot (0.09), Enflasyon (0.08)
"""

import statistics
import time
from datetime import datetime
from pathlib import Path

import pandas as pd
#diger modellerin hesaplama fonksiyonları
from app.services.fuel_service import predict_fuel_price
from app.services.inflation_service import predict_inflation
from app.services.fertilizer_service import get_commodity_price

#dizin işlemleri
KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
CSV_PATH = KOK_DIZIN / "data" / "processed" / "data_files" / "final_price_dataset.csv"

# Frontend Türkçe sezon gönderiyor, tahmin modelleri İngilizce bekliyor
SEZON_CEVIRI = {
    "İlkbahar": "Spring",
    "Yaz": "Summer",
    "Sonbahar": "Fall",
    "Kış": "Winter",
}

#AHP'ye göre
AGIRLIKLAR = {
    "kota": 0.38,
    "fiyat": 0.29,
    "gubre": 0.16,
    "mazot": 0.09,
    "enflasyon": 0.08,
}

# Takvim mevsimlerinin sırası (ay bazlı)
MEVSIM_SIRASI = {
    "Winter": 1,
    "Spring": 2,
    "Summer": 3,
    "Fall": 4,
}

# Hangi ay hangi mevsime denk geliyor
AY_MEVSIM_HARITASI = {
    12: "Winter", 1: "Winter", 2: "Winter",
    3: "Spring", 4: "Spring", 5: "Spring",
    6: "Summer", 7: "Summer", 8: "Summer",
    9: "Fall", 10: "Fall", 11: "Fall",
}

def veri_haritalarini_olustur(referans_yil_sayisi:int):
    df = pd.read_csv(CSV_PATH)

    fiyat_haritasi = {}
    for urun_adi in df["product_name"].unique():
        fiyatlar = df[df["product_name"] == urun_adi]["reel_fiyat"].tolist()
        if fiyatlar:
            fiyat_haritasi[urun_adi] = fiyatlar

    tekil = df.drop_duplicates(subset=["year", "season"])

    if referans_yil_sayisi is not None:
        son_yil = tekil["year"].max()
        tekil = tekil[tekil["year"] >= son_yil - referans_yil_sayisi]

    referans = {
        "gubre": {
            "ortalama": statistics.mean(tekil["fertilizer_price"]),
            "std": statistics.stdev(tekil["fertilizer_price"]),
        },
        "mazot": {
            "ortalama": statistics.mean(tekil["fuel_price"]),
            "std": statistics.stdev(tekil["fuel_price"]),
        },
        "enflasyon": {
            "ortalama": statistics.mean(tekil["annual_inflation"]),
            "std": statistics.stdev(tekil["annual_inflation"]),
        },
    }

    return fiyat_haritasi, referans


# Uygulama başlarken bir kez yüklenir, bellekte tutulur
FIYAT_HARITASI, REFERANS = veri_haritalarini_olustur(referans_yil_sayisi=3) #son 5 yılın verisine göre

# Gübre web'den çekildiği için basit önbellekleme (her istekte siteye gitmesin)
_GUBRE_CACHE = {"deger": None, "zaman": None}
_ONBELLEK_SURESI_SN = 6 * 60 * 60  # 6 saat

#hesaplamalar kısmı
def kota_doluluk_hesapla(kullanilan_kota: float, girilen_donum: float, maksimum_kota: float) -> float:
    yeni_kota = kullanilan_kota + girilen_donum
    if maksimum_kota <= 0:
        return 0.0
    return (yeni_kota / maksimum_kota) * 100

def cv_hesapla(degerler: list[float]) -> float:

    ortalama = statistics.mean(degerler)
    std = statistics.stdev(degerler)

    if ortalama == 0:
        return 0.0
    cv = (std / ortalama) * 100
    return min(cv, 100.0)

def sapma_riski_hesapla(deger: float, ortalama: float, std: float) -> float:
    if std == 0:
        return 0.0
    z = abs((deger - ortalama) / std)
    if z <= 0:
        return 0.0
    return min((z / 3) * 100, 100.0)


def genel_risk_hesapla(kota_doluluk: float, cv_fiyat: float,
                        gubre_riski: float, mazot_riski: float, enflasyon_riski: float) -> float:
    risk = (
        AGIRLIKLAR["kota"] * kota_doluluk +
        AGIRLIKLAR["fiyat"] * cv_fiyat +
        AGIRLIKLAR["gubre"] * gubre_riski +
        AGIRLIKLAR["mazot"] * mazot_riski +
        AGIRLIKLAR["enflasyon"] * enflasyon_riski
    )
    return min(risk, 100)


def risk_seviyesi_belirle(risk: float) -> tuple[str, str]:
    if risk <= 25:
        return "Güvenli", "🟢"
    elif risk <= 50:
        return "Orta Risk", "🟡"
    elif risk <= 75:
        return "Riskli", "🟠"
    else:
        return "Çok Riskli", "🔴"


#hesaplama için kullanılacak dış modeller ve hesaplamalar
def hedef_yil_belirle(turkce_sezon) -> int:
    """eger analiz yapılan aydan sonraki mevsim o yıl içinde var ise hala önümüzdeki yıl için degil bulundugumuz yıla göre tahmin yapıyor"""
    simdi = datetime.now()
    su_anki_mevsim = AY_MEVSIM_HARITASI[simdi.month]
    su_anki_sira = MEVSIM_SIRASI[su_anki_mevsim]

    hedef_sezon_ingilizce = sezon_cevir(turkce_sezon)
    hedef_sira = MEVSIM_SIRASI[hedef_sezon_ingilizce]

    if hedef_sira > su_anki_sira:
        return simdi.year
    else:
        return simdi.year + 1

#diger modellerde ingilizce oldugu için translate
def sezon_cevir(turkce_sezon: str) -> str:
    ingilizce = SEZON_CEVIRI.get(turkce_sezon)
    if not ingilizce:
        raise ValueError(f"Geçersiz sezon: {turkce_sezon}")
    return ingilizce


def mazot_tahmini_al(turkce_sezon: str) -> float:
    hedef_yil = hedef_yil_belirle(turkce_sezon)
    hedef_sezon = sezon_cevir(turkce_sezon)
    return predict_fuel_price(hedef_yil, hedef_sezon)


def enflasyon_tahmini_al(turkce_sezon: str) -> float:
    hedef_yil = hedef_yil_belirle(turkce_sezon)
    hedef_sezon = sezon_cevir(turkce_sezon)
    sonuc = predict_inflation(hedef_yil, hedef_sezon)
    return predict_inflation(hedef_yil, hedef_sezon)


def guncel_gubre_fiyati_getir() -> float:
    """
    Web'den güncel gübre (üre) fiyatını çeker. 6 saat önbellekler.
    Web'e erişilemezse: önceki bilinen değeri, o da yoksa tarihsel ortalamayı döner.
    """
    simdi = time.time()
    if _GUBRE_CACHE["deger"] is not None and (simdi - _GUBRE_CACHE["zaman"]) < _ONBELLEK_SURESI_SN:
        return _GUBRE_CACHE["deger"]

    try:
        fiyat = get_commodity_price("urea")
        _GUBRE_CACHE["deger"] = fiyat
        _GUBRE_CACHE["zaman"] = simdi
        return fiyat
    except Exception:
        if _GUBRE_CACHE["deger"] is not None:
            return _GUBRE_CACHE["deger"]
        return REFERANS["gubre"]["ortalama"]