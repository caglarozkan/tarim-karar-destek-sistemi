import os
import re
import unicodedata

import pandas as pd


FILES_2014_2024 = [
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
]

FILES_2025 = [
    "data/processed/data_files/cleaned_2025.csv",
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
]


def normalize_text(value):
    if pd.isna(value):
        return pd.NA

    value = str(value).strip().upper()

    mojibake_map = {
        "Ä°": "I",
        "Ä": "G",
        "Ãœ": "U",
        "Å": "S",
        "Ã–": "O",
        "Ã‡": "C",
        "Ä±": "I",
        "ÄŸ": "G",
        "Ã¼": "U",
        "ÅŸ": "S",
        "Ã¶": "O",
        "Ã§": "C",
    }

    for old, new in mojibake_map.items():
        value = value.replace(old, new)

    tr_map = str.maketrans({
        "İ": "I",
        "I": "I",
        "Ş": "S",
        "Ğ": "G",
        "Ü": "U",
        "Ö": "O",
        "Ç": "C",
        "ı": "I",
        "ş": "S",
        "ğ": "G",
        "ü": "U",
        "ö": "O",
        "ç": "C",
    })

    value = value.translate(tr_map)
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"\s+", " ", value).strip()

    return value


def standardize_product_name(value):
    value = normalize_text(value)

    product_map = {
        "DOMATES SALKIM": "DOMATES SALKIM",
        "SALATALIK SILOR": "SALATALIK SILOR",
        "KABAK TAZE": "KABAK TAZE",
        "KARPUZ": "KARPUZ",
        "SOGAN KURU": "SOGAN KURU",
        "SOĞAN KURU": "SOGAN KURU",
        "PATLICAN UZUN": "PATLICAN UZUN",
        "BIBER SIVRI": "BIBER SIVRI",
        "BIBER SİVRİ": "BIBER SIVRI",
        "BİBER SİVRİ": "BIBER SIVRI",
    }

    return product_map.get(value, value)


def normalize_column_name(value):
    value = normalize_text(value)
    value = value.replace(".", "")
    value = re.sub(r"[^A-Z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value


def read_file(path, silent=True):
    try:
        with open(path, "rb") as file:
            header = file.read(8)

        if header.startswith(b"PK\x03\x04") or header.startswith(b"\xD0\xCF\x11\xE0"):
            df = pd.read_excel(path)
            print(path, "-> Excel olarak okundu")
            return df
    except Exception:
        pass

    attempts = [
        {"encoding": "utf-8-sig", "sep": None, "engine": "python"},
        {"encoding": "cp1254", "sep": None, "engine": "python"},
        {"encoding": "iso-8859-9", "sep": None, "engine": "python"},
        {"encoding": "utf-8", "sep": None, "engine": "python"},
        {"encoding": "latin1", "sep": None, "engine": "python"},
        {"encoding": "cp1254", "sep": ";", "engine": "python"},
        {"encoding": "latin1", "sep": ";", "engine": "python"},
    ]

    for option in attempts:
        try:
            df = pd.read_csv(path, **option)

            if df.shape[1] >= 2:
                return df
        except Exception as exc:
            if not silent:
                print(path, "-> Hata:", option, "->", exc)

    print(path, "-> hiçbir yöntemle okunamadı")
    return None


def extract_year_from_path(path):
    file_name = os.path.basename(path)
    match = re.search(r"(20\d{2})", file_name)

    if not match:
        return pd.NA

    return int(match.group(1))


def rename_columns(df):
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


def parse_date(series):
    series = series.astype(str).str.strip()

    date = pd.to_datetime(series, errors="coerce", format="%Y-%m-%d")

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(series.loc[mask], errors="coerce", format="%d/%m/%Y")

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(series.loc[mask], errors="coerce", format="%m/%d/%Y")

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(series.loc[mask], errors="coerce", format="%m/%d/%Y %H:%M:%S")

    mask = date.isna()
    date.loc[mask] = pd.to_datetime(series.loc[mask], errors="coerce", dayfirst=True)

    return date


def get_season(month):
    if pd.isna(month):
        return pd.NA

    month = int(month)

    if month in [12, 1, 2]:
        return "Winter"
    if month in [3, 4, 5]:
        return "Spring"
    if month in [6, 7, 8]:
        return "Summer"
    return "Fall"


def to_numeric(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", ".", regex=False).str.strip(),
        errors="coerce"
    )


def clean_file(path):
    df = read_file(path)

    if df is None:
        return None

    df = rename_columns(df)
    df = df.dropna(how="all").reset_index(drop=True)

    file_year = extract_year_from_path(path)

    for column in ["date", "product_type", "product_name", "unit", "min_price", "max_price", "average_price", "year"]:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[["date", "product_type", "product_name", "unit", "min_price", "max_price", "average_price", "year"]]

    df = df[df["product_name"].notna()]
    df = df[normalize_text("product_name") != df["product_name"].astype(str).apply(normalize_text)]

    df["date"] = parse_date(df["date"])

    if df["year"].isna().all():
        df["year"] = file_year

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df.loc[df["year"].isna(), "year"] = file_year

    for column in ["min_price", "max_price", "average_price"]:
        df[column] = to_numeric(df[column])

    df["product_name"] = df["product_name"].apply(standardize_product_name)
    df["product_type"] = df["product_type"].apply(normalize_text)
    df["unit"] = df["unit"].apply(normalize_text)

    df["month"] = df["date"].dt.month
    df["season"] = df["month"].apply(get_season)

    date_year = df["date"].dt.year
    df.loc[date_year.notna(), "year"] = date_year

    # Aralık ayı bir sonraki yılın Winter sezonuna aittir.
    df.loc[df["month"] == 12, "year"] += 1

    df = df.dropna(subset=["date", "product_name", "average_price", "year", "season"])
    df["year"] = df["year"].astype(int)

    df = df[df["product_name"].isin(PRODUCTS)].copy()

    return df[TARGET_COLUMNS].reset_index(drop=True)


def build_marketplace_dataset():
    all_frames = []

    for path in FILES_2014_2024 + FILES_2025:
        df = clean_file(path)

        if df is not None and not df.empty:
            all_frames.append(df)
            print(path, "eklendi:", df.shape, "NaT sayısı:", df["date"].isna().sum())
        else:
            print(path, "boş veya okunamadı")

    if not all_frames:
        raise ValueError("Hiçbir dosyadan veri okunamadı.")

    final_df = pd.concat(all_frames, ignore_index=True)
    final_df = final_df.drop_duplicates()

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    return final_df


if __name__ == "__main__":
    marketplace = build_marketplace_dataset()

    print("Temiz marketplace dosyası oluşturuldu:", OUTPUT_PATH)
    print("Satır sayısı:", len(marketplace))
    print("Kolonlar:", list(marketplace.columns))
    print(marketplace.head())
