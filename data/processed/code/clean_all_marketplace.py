import os
import re
import unicodedata
import pandas as pd


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
    "data/processed/data_files/cleaned_2025.csv",
    "data/processed/data_files/cleaned_2026.csv",
]

OUTPUT_PATH = "data/processed/data_files/cleaned_all_marketplace.csv"

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


PRODUCTS = [
    "DOMATES SALKIM",
    "SALATALIK SILOR",
    "KABAK TAZE",
    "KARPUZ",
    "SOGAN KURU",
    "PATLICAN UZUN",
    "BIBER SIVRI",
    "KARNABAHAR",
    "LAHANA BEYAZ",
    "MARUL",
    "PIRASA",
    "LAHANA KIRMIZI",
    "BAKLA",
    "BEZELYE",
    "ISPANAK",
    "BROKOLI",
]


def normalize_text(value):
    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    value = (
        value
        .replace("İ", "I")
        .replace("ı", "I")
        .replace("Ş", "S")
        .replace("ş", "S")
        .replace("Ğ", "G")
        .replace("ğ", "G")
        .replace("Ü", "U")
        .replace("ü", "U")
        .replace("Ö", "O")
        .replace("ö", "O")
        .replace("Ç", "C")
        .replace("ç", "C")
    )

    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"\s+", " ", value).strip()

    return value


def standardize_product_name(value):
    value = normalize_text(value)

    product_map = {
        "DOMATES SALKIM": "DOMATES SALKIM",
        "DOMATES SOFRALIK": "DOMATES SALKIM",

        "SALATALIK SILOR": "SALATALIK SILOR",
        "SALATALIK SİLOR": "SALATALIK SILOR",
        "HIYAR SOFRALIK": "SALATALIK SILOR",

        "KABAK SAKIZ": "KABAK TAZE",
        "KABAK TAZE": "KABAK TAZE",

        "KARPUZ": "KARPUZ",

        "SOGAN KURU": "SOGAN KURU",
        "SOĞAN KURU": "SOGAN KURU",

        "PATLICAN": "PATLICAN UZUN",
        "PATLICAN UZUN": "PATLICAN UZUN",

        "BIBER SIVRI": "BIBER SIVRI",
        "BİBER SİVRİ": "BIBER SIVRI",
    
  
       "PATLICAN UZUN": "PATLICAN UZUN",
       "KARNABAHAR": "KARNABAHAR",
       "LAHANA BEYAZ": "LAHANA BEYAZ",
       "MARUL": "MARUL",
       "PIRASA": "PIRASA",
       "LAHANA KIRMIZI": "LAHANA KIRMIZI",
       "BAKLA": "BAKLA",
       "BEZELYE": "BEZELYE",
       "ISPANAK": "ISPANAK",
       "BROKOLI": "BROKOLI",
}
    

    return product_map.get(value, value)


def normalize_column_name(value):
    value = normalize_text(value)
    value = value.replace(".", "")
    value = re.sub(r"[^A-Z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def read_file(dosya, sessiz=True):
    try:
        with open(dosya, "rb") as file:
            header = file.read(8)

        if header.startswith(b"PK\x03\x04") or header.startswith(b"\xD0\xCF\x11\xE0"):
            df = pd.read_excel(dosya)
            print(dosya, "-> Excel olarak okundu")
            return df
    except Exception:
        pass

    attempts = [
        {"encoding": "utf-8-sig", "sep": None, "engine": "python"},
        {"encoding": "cp1254", "sep": None, "engine": "python"},
        {"encoding": "iso-8859-9", "sep": None, "engine": "python"},
        {"encoding": "utf-8", "sep": None, "engine": "python"},
        {"encoding": "latin1", "sep": None, "engine": "python"},
        {"encoding": "utf-8-sig", "sep": ",", "engine": "python"},
        {"encoding": "utf-8-sig", "sep": ";", "engine": "python"},
        {"encoding": "utf-8-sig", "sep": "|", "engine": "python"},
        {"encoding": "cp1254", "sep": ";", "engine": "python"},
        {"encoding": "latin1", "sep": ";", "engine": "python"},
    ]

    for option in attempts:
        try:
            df = pd.read_csv(dosya, **option)

            df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

            if df.shape[1] >= 2:
                return df

        except Exception as exc:
            if not sessiz:
                print(dosya, "-> Hata:", option, "->", exc)

    print(dosya, "-> hiçbir yöntemle okunamadı")
    return None


def find_year(file):
    file_name = os.path.basename(file)
    match = re.search(r"(20\d{2})", file_name)

    if not match:
        return pd.NA

    return int(match.group(1))


def manage_columns(df):
    df = df.copy()
    df.columns = [normalize_column_name(col) for col in df.columns]

    rename_map = {
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
        "AVG_PRICE": "average_price",
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

        "YIL": "year",
        "YEAR": "year",
    }

    return df.rename(columns=rename_map)


def manage_date(series):
    series = series.astype(str).str.strip()

    date = pd.to_datetime(series, errors="coerce", format="%Y-%m-%d")

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(
        series.loc[mask],
        errors="coerce",
        format="%d/%m/%Y"
    )

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(
        series.loc[mask],
        errors="coerce",
        format="%m/%d/%Y"
    )

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(
        series.loc[mask],
        errors="coerce",
        format="%m/%d/%Y %H:%M:%S"
    )

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(
        series.loc[mask],
        errors="coerce",
        dayfirst=True
    )

    return date


def find_season(month):
    if pd.isna(month):
        return pd.NA

    month = int(month)

    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Fall"


def to_numeric(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False).str.strip(),
        errors="coerce"
    )


def clean_file(file):
    df = read_file(file)

    if df is None:
        return None

    df = manage_columns(df)
    df = df.dropna(how="all").reset_index(drop=True)

    year = find_year(file)

    for column in [
        "date",
        "product_type",
        "product_name",
        "unit",
        "min_price",
        "max_price",
        "average_price",
        "year",
    ]:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[
        [
            "date",
            "product_type",
            "product_name",
            "unit",
            "min_price",
            "max_price",
            "average_price",
            "year",
        ]
    ]

    df = df[df["product_name"].notna()]
    df = df[df["product_name"].astype(str).apply(normalize_text) != "PRODUCT_NAME"]

    df["date"] = manage_date(df["date"])

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df.loc[df["year"].isna(), "year"] = year

    for column in ["min_price", "max_price", "average_price"]:
        df[column] = to_numeric(df[column])

    df.loc[df["average_price"].isna(), "average_price"] = (
        df["min_price"] + df["max_price"]
    ) / 2

    df["product_name"] = df["product_name"].apply(standardize_product_name)
    df["product_type"] = df["product_type"].apply(normalize_text)
    df["unit"] = df["unit"].apply(normalize_text)

    df["month"] = df["date"].dt.month
    df["season"] = df["month"].apply(find_season)

    date_year = df["date"].dt.year
    df.loc[date_year.notna(), "year"] = date_year

    df.loc[df["month"] == 12, "year"] += 1

    df = df.dropna(
        subset=["date", "product_name", "average_price", "year", "season"]
    )

    df["year"] = df["year"].astype(int)

    df = df[df["product_name"].isin(PRODUCTS)].copy()

    return df[TARGET_COLUMNS].reset_index(drop=True)


all_files = []

for file in FILES:
    df = clean_file(file)

    if df is not None and not df.empty:
        all_files.append(df)
        print(file, "eklendi:", df.shape)
        print("NaT sayısı:", df["date"].isna().sum())
    else:
        print(file, "boş veya okunamadı")


if not all_files:
    raise ValueError("Hiçbir dosyadan veri okunamadı.")

df_final = pd.concat(all_files, ignore_index=True)
df_final = df_final.drop_duplicates().reset_index(drop=True)

df_final.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

df_final=df_final.drop(columns=["product_type","unit"]).reset_index(drop=True)

print(df_final.sample(10))