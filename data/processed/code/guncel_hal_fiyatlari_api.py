import time
from datetime import date

import pandas as pd
import requests


BASE_URL = (
    "https://openapi.izmir.bel.tr/"
    "api/ibb/halfiyatlari/sebzemeyve/{}"
)


def listeyi_bul(json_verisi):
    """
    API doğrudan liste veya bir sözlük içerisinde liste döndürürse
    ürün kayıtlarını bulur.
    """
    if isinstance(json_verisi, list):
        return json_verisi

    if isinstance(json_verisi, dict):
        # Muhtemel cevap anahtarları
        for anahtar in ["data", "result", "results", "sebzemeyve"]:
            deger = json_verisi.get(anahtar)

            if isinstance(deger, list):
                return deger

        # İsmi bilinmeyen ilk listeyi bul
        for deger in json_verisi.values():
            if isinstance(deger, list):
                return deger

    return []


def gunluk_veri_cek(tarih, session):
    tarih_metni = tarih.strftime("%Y-%m-%d")
    url = BASE_URL.format(tarih_metni)

    try:
        response = session.get(url, timeout=30)

        # O gün için veri bulunmayabilir
        if response.status_code in [204, 404]:
            return []

        response.raise_for_status()

        kayitlar = listeyi_bul(response.json())

        for kayit in kayitlar:
            # API tarih alanı döndürmüyorsa kendimiz ekliyoruz
            kayit["Tarih"] = tarih_metni

        return kayitlar

    except requests.RequestException as hata:
        print(f"{tarih_metni} alınamadı: {hata}")
        return []

    except ValueError:
        print(f"{tarih_metni}: JSON cevabı okunamadı.")
        return []


baslangic = pd.Timestamp("2026-01-01")

# Dosya çalıştırıldığı güne kadar veri toplar
bitis = pd.Timestamp(date.today())

tarihler = pd.date_range(
    start=baslangic,
    end=bitis,
    freq="D"
)

tum_kayitlar = []

with requests.Session() as session:
    session.headers.update({
        "User-Agent": "Izmir-Tarim-Analizi/1.0"
    })

    for sira, tarih in enumerate(tarihler, start=1):
        kayitlar = gunluk_veri_cek(tarih, session)
        tum_kayitlar.extend(kayitlar)

        print(
            f"{sira}/{len(tarihler)} - "
            f"{tarih.date()} - {len(kayitlar)} kayıt"
        )

        # API'ye çok hızlı istek göndermemek için
        time.sleep(0.15)


df_2026 = pd.DataFrame(tum_kayitlar)

if df_2026.empty:
    print("2026 için veri alınamadı.")

else:
    print("API kolonları:", df_2026.columns.tolist())

    # Olası kolon isimlerini standartlaştır
    kolon_eslestirme = {
        "Tarih": "TARIH",
        "MalAdi": "MAL_ADI",
        "MalTipAdi": "MAL_TIPI",
        "HalTuru": "HAL_TURU",
        "Birim": "BIRIM",
        "AsgariUcret": "ASGARI_FIYAT",
        "AzamiUcret": "AZAMI_FIYAT"
    }

    df_2026 = df_2026.rename(columns=kolon_eslestirme)

    # Tarihi datetime yap
    df_2026["TARIH"] = pd.to_datetime(
        df_2026["TARIH"],
        errors="coerce"
    )

    # Fiyatları sayıya çevir
    fiyat_kolonlari = [
        "ASGARI_FIYAT",
        "AZAMI_FIYAT"
    ]

    for kolon in fiyat_kolonlari:
        if kolon in df_2026.columns:
            df_2026[kolon] = pd.to_numeric(
                df_2026[kolon],
                errors="coerce"
            )

    # API ortalama fiyat vermiyorsa hesapla
    if {
        "ASGARI_FIYAT",
        "AZAMI_FIYAT"
    }.issubset(df_2026.columns):

        df_2026["ORTALAMA_FIYAT"] = (
            df_2026["ASGARI_FIYAT"]
            + df_2026["AZAMI_FIYAT"]
        ) / 2

        df_2026["ORTALAMA_FIYAT"] = (
            df_2026["ORTALAMA_FIYAT"].round(2)
        )

    # Tamamen aynı kayıtları kaldır
    df_2026 = df_2026.drop_duplicates()

    # Tarihe ve ürüne göre sırala
    siralama = [
        kolon
        for kolon in ["TARIH", "MAL_ADI"]
        if kolon in df_2026.columns
    ]

    df_2026 = df_2026.sort_values(siralama)

    dosya_adi = "data/raw_data//marketplace_data/izbb_hal_fiyatlari_2026_gecici.csv"

    df_2026.to_csv(
        dosya_adi,
        index=False,
        encoding="utf-8-sig"
    )

    print(f"\nDosya oluşturuldu: {dosya_adi}")
    print(f"Toplam kayıt: {len(df_2026)}")
    print(
        "Tarih aralığı:",
        df_2026["TARIH"].min(),
        "-",
        df_2026["TARIH"].max()
    )