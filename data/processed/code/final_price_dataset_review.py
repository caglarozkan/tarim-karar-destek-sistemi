import pandas as pd
import numpy as np


INPUT_PATH = "data/processed/data_files/cleaned_all_marketplace.csv"
OUTPUT_PATH = "data/processed/data_files/final_price_dataset.csv"

market = pd.read_csv(INPUT_PATH)


market = market.rename(columns={
    "TARIH": "date",
    "URUN_ADI": "product_name",
    "ORTALAMA_FIYAT": "average_price",
    "ASGARI_FIYAT": "min_price",
    "AZAMI_FIYAT": "max_price",
    "BIRIM": "unit",
    "YIL": "year",
    "SEZON": "season",

    "Tarih": "date",
    "Urun_Adi": "product_name",
    "Ortalama_Fiyat": "average_price",
})


market["date"] = pd.to_datetime(
    market["date"],
    errors="coerce"
)

market["year"] = market["date"].dt.year
market["month"] = market["date"].dt.month


def get_season(month):
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


market["season"] = market["month"].apply(get_season)


market["product_name"] = (
    market["product_name"]
    .astype(str)
    .str.upper()
    .str.strip()
)

market["product_name"] = (
    market["product_name"]
    .str.replace("İ", "I", regex=False)
    .str.replace("Ş", "S", regex=False)
    .str.replace("Ğ", "G", regex=False)
    .str.replace("Ü", "U", regex=False)
    .str.replace("Ö", "O", regex=False)
    .str.replace("Ç", "C", regex=False)
)

market["product_name"] = market["product_name"].str.replace(
    r"\s+",
    " ",
    regex=True
)


PRODUCT_NAME_MAP = {
    "DOMATES SALKIM": "DOMATES SALKIM",
    "SALATALIK SILOR": "SALATALIK SILOR",
    "KABAK SAKIZ": "KABAK TAZE",
    "KABAK TAZE": "KABAK TAZE",
    "KARPUZ": "KARPUZ",
    "SOGAN KURU": "SOGAN KURU",
    "BIBER SIVRI": "BIBER SIVRI",
    "PATLICAN UZUN": "PATLICAN UZUN",
    "PATLICAN": "PATLICAN UZUN",
    "KARNABAHAR":"KARNABAHAR",
    "LAHANA  BEYAZ":"LAHANA BEYAZ",
    "MARUL":"MARUL",
    "PIRASA":"PIRASA",
    "LAHANA  KIRMIZI":"LAHANA KIRMIZI",
    "BAKLA":"BAKLA",
    "BEZELYE":"BEZELYE",
    "ISPANAK":"ISPANAK",
    "BROKOLI":"BROKOLI"
}

market["product_name"] = (
    market["product_name"]
    .replace(PRODUCT_NAME_MAP)
)

allowed_products = [
    "DOMATES SALKIM",
    "SALATALIK SILOR",
    "KABAK TAZE",
    "KARPUZ",
    "SOGAN KURU",
    "BIBER SIVRI",
    "PATLICAN UZUN",
    "KARNABAHAR",
    "LAHANA BEYAZ",
    "MARUL",
    "PIRASA",
    "LAHANA KIRMIZI",
    "BAKLA",
    "BEZELYE",
    "ISPANAK",
    "BROKOLI"
]

market["average_price"] = pd.to_numeric(
    market["average_price"],
    errors="coerce"
)

market = market[
    market["product_name"].isin(allowed_products)
]

market = market[
    market["average_price"].notna()
    & market["year"].notna()
    & market["season"].notna()
]

price_table = (
    market
    .groupby(
        ["product_name", "year", "season"],
        as_index=False
    )
    .agg(
        average_price=("average_price", "mean")
    )
)

price_table["average_price"] = price_table["average_price"].round(2)
SEASON_ORDER = {
    "Winter": 1,
    "Spring": 2,
    "Summer": 3,
    "Fall": 4
}

price_table["season_order"] = price_table["season"].map(SEASON_ORDER)

price_table = price_table.sort_values(
    ["product_name", "year", "season_order"]
).reset_index(drop=True)

price_table = price_table.drop(columns=["season_order"])


price_table.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("final_price_dataset.csv oluşturuldu.")
print(price_table.head(20))