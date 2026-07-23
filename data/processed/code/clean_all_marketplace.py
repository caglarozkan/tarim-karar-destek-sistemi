import pandas as pd
import numpy as np
import re

FILES = [
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
    "data/processed/data_files/cleaned_2024.csv",
    "data/processed/data_files/cleaned_2026.csv"
]
FILE2=["data/processed/data_files/cleaned_2025.csv"]

TARGET_COLUMNS = [
    "date",
    "product_type",
    "product_name",
    "unit",
    "min_price",
    "max_price",
    "average_price",
    "year",
    "month",
    "season",
]


def read_file(dosya, sessiz=True):
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


def find_year(file):
    return int(file.split("/")[-1].split("_")[-1].split(".")[0])


def manage_columns(df):
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
        "ASGARI_UCRET": "min_price",
        "ASGARI_FIYATI": "min_price",
        "ASGARI_FIYAT": "min_price",
        "MIN_PRICE": "min_price",

        "AZAMI_UCRET": "max_price",
        "AZAMI_FIYATI": "max_price",
        "AZAMI_FIYAT": "max_price",
        "MAX_PRICE": "max_price",

        "ORTALAMA_UCRET": "average_price",
        "ORTALAMA_FIYATI": "average_price",
        "ORTALAMA_FIYAT": "average_price",
        "ORT_FIYAT": "average_price",
        "AVERAGE_PRICE": "average_price",

        "MAL_ADI": "product_name",
        "URUN_ADI": "product_name",
        "PRODUCT_NAME": "product_name",

        "BULTEN_TARIHI": "date",
        "TARIH": "date",
        "DATE": "date",

        "MAL_TIPI": "product_type",
        "MAL_TURU": "product_type",
        "PRODUCT_TYPE": "product_type",

        "BIRIMI": "unit",
        "BIRIM": "unit",
        "UNIT": "unit",
    })

    return df

def manage_date(s):
    s = s.astype(str).str.strip()
    date= pd.to_datetime(
        s,
        errors="coerce",
        format="%m/%d/%Y"
    )

    mask =date.isna()
    date.loc[mask] = pd.to_datetime(
        s.loc[mask],
        errors="coerce",
        format="%m/%d/%Y %H:%M:%S"
    )

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(
        s.loc[mask],
        errors="coerce",
        dayfirst=False
    )

    return date



def regulate_after_2025(df):
    
    df["date"] = pd.to_datetime(
        df["date"],
        format="%d/%m/%Y",        
        errors="coerce"
    )

    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    def find_season(month):
        if pd.isna(month):
            return pd.NA
        elif month in [12, 1, 2]:
            return "Winter"
        elif month in [3, 4, 5]:
            return "Spring"
        elif month in [6, 7, 8]:
            return "Summer"
        else:
            return "Fall"

    df["season"] = df["month"].apply(find_season)

    return df
    
def find_season(month):
    if pd.isna(month):
        return pd.NA

    month= int(month)

    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Fall"


def clean_file(file):
    df = read_file(file)

    if df is None:
        return None

    df = manage_columns(df)
    df = df.dropna(how="all").reset_index(drop=True)

    year= find_year(file)
    df["year"] = year

    for column in TARGET_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[TARGET_COLUMNS]

    df = df[df["product_name"].notna()]
    df = df[df["product_name"].astype(str).str.upper() != "product_name"]

    df["date"] = manage_date(df["date"])

    for column in ["min_price", "max_price", "average_price"]:
        df[column] = (
            df[column]
            .astype(str)
            .str.replace(",", ".", regex=False)
        )
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df["month"] = df["date"].dt.month
    df["season"] = df["month"].apply(find_season)

    return df.reset_index(drop=True)


all_files = []

for file in FILES:
    df = clean_file(file)

    if df is not None and not df.empty:
        all_files.append(df)
        print(file, "eklendi:", df.shape)
        print("NaT sayısı:", df["date"].isna().sum())
    else:
        print(file, "boş veya okunamadı")
        
for file in FILE2:
    df = clean_file(file)

    if df is not None and not df.empty:
        all_files.append(df)
        print(file, "eklendi:", df.shape)
        print("NaT sayısı:", df["date"].isna().sum())
    else:
        print(file, "boş veya okunamadı")
        
df_final = pd.concat(all_files, ignore_index=True)

df_final.to_csv("data/processed/data_files/cleaned_all_marketplace.csv",index=False)
