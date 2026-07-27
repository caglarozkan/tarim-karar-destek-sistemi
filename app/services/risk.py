"""
risk.py
Risk analizi hesaplama modülü.
AHP (Analytic Hierarchy Process) ile belirlenmiş ağırlıklara göre
5 faktörden oluşan bileşik bir risk skoru üretir:
Kota (0.38), Fiyat (0.29), Gübre (0.16), Mazot (0.09), Enflasyon (0.08)

NOT: CV ve z-score hesaplamasından ÖNCE fiyatlar enflasyona göre
"reel" hale getiriliyor - yoksa Türkiye'deki sürekli enflasyon
yüzünden fiyatlar hep yukarı gittiği için bu artış "oynaklık/risk"
gibi algılanır ve skorlar hep 100'e yakın çıkar.
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


def enflasyon_endeksi_ekle(df: pd.DataFrame) -> pd.DataFrame:
    """
    Endeksi SADECE tekil (year, season) satirlari uzerinde kurar,
    sonra bunu tum df'ye dict-tabanli esleme ile geri yansitir.
    annual_inflation'da eksik (NaN) deger varsa, o donem icin
    'degisim yok' (0) varsayilir - yoksa carpimsal zincir bir kere
    NaN'a dusunce tum sonraki degerler de NaN olur.
    """
    df = df.copy()
    df["season_order"] = df["season"].map(MEVSIM_SIRASI)

    tekil = df.drop_duplicates(subset=["year", "season"]).copy()
    tekil = tekil.sort_values(["year", "season_order"]).reset_index(drop=True)

    # eksik enflasyon degerini 0 kabul et (o donem icin fiyat degismedi varsayimi)
    tekil["annual_inflation"] = tekil["annual_inflation"].fillna(0)

    ceyreklik_carpan = 1 + (tekil["annual_inflation"] / 100 / 4)
    # ilk donemin carpani onemsiz (referans nokta), kumulatif urun bir onceki
    # donemin degerine gore ilerlemeli, o yuzden 1 kaydiriyoruz
    kumulatif = ceyreklik_carpan.shift(1).fillna(1).cumprod()

    tekil["endeks"] = kumulatif
    son_endeks = tekil["endeks"].iloc[-1]
    if son_endeks == 0 or pd.isna(son_endeks):
        son_endeks = 1.0
    tekil["endeks"] = tekil["endeks"] / son_endeks

    endeks_sozlugu = {}
    for _, satir in tekil.iterrows():
        anahtar = (str(satir["year"]), str(satir["season"]))
        endeks_sozlugu[anahtar] = satir["endeks"]

    df["endeks"] = df.apply(
        lambda satir: endeks_sozlugu.get((str(satir["year"]), str(satir["season"])), 1.0),
        axis=1
    )

    return df

def veri_haritalarini_olustur(referans_yil_sayisi: int | None):
    df = pd.read_csv(CSV_PATH)
    df = enflasyon_endeksi_ekle(df)

    # Reel (enflasyondan arındırılmış) değerler
    df["reel_fiyat"] = df["average_price"] / df["endeks"]
    df["reel_gubre"] = df["fertilizer_price"] / df["endeks"]
    df["reel_mazot"] = df["fuel_price"] / df["endeks"]

    fiyat_haritasi = {}
    for urun_adi in df["product_name"].unique():
        fiyatlar = df[df["product_name"] == urun_adi]["reel_fiyat"].dropna().tolist()
        if len(fiyatlar) >= 2:
            fiyat_haritasi[urun_adi] = fiyatlar

    tekil = df.drop_duplicates(subset=["year", "season"])

    if referans_yil_sayisi is not None:
        son_yil = tekil["year"].max()
        tekil = tekil[tekil["year"] >= son_yil - referans_yil_sayisi]

    referans = {
        "gubre": {
            "ortalama": tekil["reel_gubre"].mean(),
            "std": tekil["reel_gubre"].std(),
        },
        "mazot": {
            "ortalama": tekil["reel_mazot"].mean(),
            "std": tekil["reel_mazot"].std(),
        },
        "enflasyon": {
            "ortalama": tekil["annual_inflation"].mean(),
            "std": tekil["annual_inflation"].std(),
        },
    }

    return fiyat_haritasi, referans


# Uygulama başlarken bir kez yüklenir, bellekte tutulur.
# Referans penceresi tüm geçmiş veri (None = filtre yok) - dar pencerede
# standart sapma güvenilmez çıktığı için tüm veriye genişletildi.
FIYAT_HARITASI, REFERANS = veri_haritalarini_olustur(referans_yil_sayisi=None)

# Gübre web'den çekildiği için basit önbellekleme (her istekte siteye gitmesin)
_GUBRE_CACHE = {"deger": None, "zaman": None}
_ONBELLEK_SURESI_SN = 6 * 60 * 60  # 6 saat

#hesaplamalar kısmı
def kota_doluluk_hesapla(kullanilan_kota: float, girilen_donum: float, maksimum_kota: float) -> float:
    yeni_kota = kullanilan_kota + girilen_donum
    if maksimum_kota <= 0:
        return 0.0
    doluluk = (yeni_kota / maksimum_kota) * 100
    return min(doluluk, 100.0)


def cv_hesapla(degerler: list[float]) -> float:
    ortalama = statistics.mean(degerler)
    std = statistics.stdev(degerler)

    if ortalama == 0:
        return 0.0
    cv = (std / ortalama) * 100
    return min(cv, 100.0)


def sapma_riski_hesapla(deger: float, ortalama: float, std: float) -> float:
    if std == 0 or pd.isna(std):
        return 0.0
    z = abs((deger - ortalama) / std)
    return min((z / 5) * 100, 100.0)


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