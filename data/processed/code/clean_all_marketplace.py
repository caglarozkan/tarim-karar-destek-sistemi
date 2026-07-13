import pandas as pd
import numpy as np
import re

dosyalar = [
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2014.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2015.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2016.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2017.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2018.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2019.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2020.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2021.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2022.csv",
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2023.csv",
    "data/processed/cleaned_2024.csv"
]
dosyalar2=["data/processed/cleaned_2025.csv"]

HEDEF_KOLONLAR = [
    "TARIH",
    "MAL_TURU",
    "URUN_ADI",
    "BIRIM",
    "ASGARI_FIYAT",
    "AZAMI_FIYAT",
    "ORTALAMA_FIYAT",
    "YIL"
]


def dosya_oku(dosya, sessiz=True):
    try:
        with open(dosya, "rb") as f:
            header = f.read(8)

        if header.startswith(b"PK\x03\x04") or header.startswith(b"\xD0\xCF\x11\xE0"):
            df = pd.read_excel(dosya)
            print(dosya, "-> Excel olarak okundu")
            return df
    except Exception:
        pass

    denemeler = [
        {"encoding": "utf-8-sig", "sep": None, "engine": "python"},
        {"encoding": "cp1254", "sep": None, "engine": "python"},
        {"encoding": "iso-8859-9", "sep": None, "engine": "python"},
        {"encoding": "utf-8", "sep": None, "engine": "python"},
        {"encoding": "latin1", "sep": None, "engine": "python"},
        {"encoding": "cp1254", "sep": ";", "engine": "python"},
        {"encoding": "latin1", "sep": ";", "engine": "python"},
    ]

    for secenek in denemeler:
        try:
            df = pd.read_csv(dosya, **secenek)

            if df.shape[1] < 2:
                continue

            return df

        except Exception as e:
            if not sessiz:
                print(dosya, "-> Hata:", secenek, "->", e)

    print(dosya, "-> HİÇBİR YÖNTEMLE OKUNAMADI")
    return None


def yil_bul(dosya):
    return int(dosya.split("/")[-1].split("_")[-1].split(".")[0])


def kolonlari_duzenle(df):
    df = df.copy()

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace("İ", "I", regex=False)
        .str.replace("Ğ", "G", regex=False)
        .str.replace("Ü", "U", regex=False)
        .str.replace("Ş", "S", regex=False)
        .str.replace("Ö", "O", regex=False)
        .str.replace("Ç", "C", regex=False)
        .str.replace(" ", "_", regex=False)
        .str.replace(".", "", regex=False)
    )

    df = df.rename(columns={
        "ASGARI_UCRET": "ASGARI_FIYAT",
        "ASGARI_FIYATI": "ASGARI_FIYAT",
        "ASGARI_FIYAT": "ASGARI_FIYAT",

        "AZAMI_UCRET": "AZAMI_FIYAT",
        "AZAMI_FIYATI": "AZAMI_FIYAT",
        "AZAMI_FIYAT": "AZAMI_FIYAT",

        "ORTALAMA_UCRET": "ORTALAMA_FIYAT",
        "ORTALAMA_FIYATI": "ORTALAMA_FIYAT",
        "ORTALAMA_FIYAT": "ORTALAMA_FIYAT",
        "ORT_FIYAT": "ORTALAMA_FIYAT",

        "MAL_ADI": "URUN_ADI",
        "URUN_ADI": "URUN_ADI",

        "BULTEN_TARIHI": "TARIH",
        "TARIH": "TARIH",

        "MAL_TIPI": "MAL_TURU",
        "MAL_TURU": "MAL_TURU",

        "BIRIMI": "BIRIM",
        "BIRIM": "BIRIM"
    })

    return df


def tarih_duzenle(s):
    s = s.astype(str).str.strip()
    tarih = pd.to_datetime(
        s,
        errors="coerce",
        format="%m/%d/%Y"
    )

    mask = tarih.isna()
    tarih.loc[mask] = pd.to_datetime(
        s.loc[mask],
        errors="coerce",
        format="%m/%d/%Y %H:%M:%S"
    )

    mask = tarih.isna()
    tarih.loc[mask] = pd.to_datetime(
        s.loc[mask],
        errors="coerce",
        dayfirst=False
    )

    return tarih



def tarih_duzenle_2025_sonrasi(df):
    
    df["TARIH"] = pd.to_datetime(
        df["TARIH"],
        format="%d/%m/%Y",        
        errors="coerce"
    )

    df["YIL"] = df["TARIH"].dt.year
    df["AY"] = df["TARIH"].dt.month

    def sezon_bul(ay):
        if pd.isna(ay):
            return pd.NA
        elif ay in [12, 1, 2]:
            return "Winter"
        elif ay in [3, 4, 5]:
            return "Spring"
        elif ay in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"

    df["SEZON"] = df["AY"].apply(sezon_bul)

    return df
    
def sezon_bul(ay):
    if pd.isna(ay):
        return pd.NA

    ay = int(ay)

    if ay in [12, 1, 2]:
        return "Winter"
    elif ay in [3, 4, 5]:
        return "Spring"
    elif ay in [6, 7, 8]:
        return "Summer"
    else:
        return "Fall"


def dosya_temizle(dosya):
    df = dosya_oku(dosya)

    if df is None:
        return None

    df = kolonlari_duzenle(df)
    df = df.dropna(how="all").reset_index(drop=True)

    yil = yil_bul(dosya)
    df["YIL"] = yil

    for kolon in HEDEF_KOLONLAR:
        if kolon not in df.columns:
            df[kolon] = pd.NA

    df = df[HEDEF_KOLONLAR]

    df = df[df["URUN_ADI"].notna()]
    df = df[df["URUN_ADI"].astype(str).str.upper() != "URUN_ADI"]

    df["TARIH"] = tarih_duzenle(df["TARIH"])

    for kolon in ["ASGARI_FIYAT", "AZAMI_FIYAT", "ORTALAMA_FIYAT"]:
        df[kolon] = (
            df[kolon]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        df[kolon] = pd.to_numeric(df[kolon], errors="coerce")

    df["AY"] = df["TARIH"].dt.month
    df["SEZON"] = df["AY"].apply(sezon_bul)

    return df.reset_index(drop=True)


tum_dosyalar = []

for dosya in dosyalar:
    df = dosya_temizle(dosya)

    if df is not None and not df.empty:
        tum_dosyalar.append(df)
        print(dosya, "eklendi:", df.shape)
        print("NaT sayısı:", df["TARIH"].isna().sum())
    else:
        print(dosya, "boş veya okunamadı")
        
for dosya in dosyalar2:
    df = dosya_temizle(dosya)

    if df is not None and not df.empty:
        tum_dosyalar.append(df)
        print(dosya, "eklendi:", df.shape)
        print("NaT sayısı:", df["TARIH"].isna().sum())
    else:
        print(dosya, "boş veya okunamadı")
        
df_final = pd.concat(tum_dosyalar, ignore_index=True)

df_final.to_csv("data/processed/cleaned_all_marketplace.csv")
