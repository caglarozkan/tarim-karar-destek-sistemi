import os
import re
import unicodedata

import pandas as pd


MARKET_PATH = "data/processed/data_files/cleaned_all_marketplace.csv"
INFLATION_PATH = "data/processed/data_files/seasonal_inflation.csv"
FUEL_PATH = "data/processed/data_files/seasonal_fuel_prices.csv"
FERTILIZER_PATH = "data/processed/data_files/cleaned_fertilizer.csv"
PLANTED_PATH = "data/processed/data_files/cleaned_tuik.csv"
OUTPUT_PATH = "data/processed/data_files/final_price_dataset.csv"

PRODUCTS = [
    "DOMATES SALKIM",
    "SALATALIK SILOR",
    "KABAK TAZE",
    "KARPUZ",
    "SOGAN KURU",
    "PATLICAN UZUN",
    "BIBER SIVRI",
]

SEASON_ORDER = {
    "Winter": 1,
    "Spring": 2,
    "Summer": 3,
    "Fall": 4,
}


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


def normalize_season(value):
    if pd.isna(value):
        return pd.NA

    value = normalize_text(value)

    season_map = {
        "WINTER": "Winter",
        "KIS": "Winter",
        "SPRING": "Spring",
        "ILKBAHAR": "Spring",
        "SUMMER": "Summer",
        "YAZ": "Summer",
        "FALL": "Fall",
        "AUTUMN": "Fall",
        "SONBAHAR": "Fall",
    }

    return season_map.get(value, value.title())


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


def rename_if_exists(df, rename_map):
    existing_map = {
        old: new
        for old, new in rename_map.items()
        if old in df.columns and new not in df.columns
    }

    return df.rename(columns=existing_map)


def load_data():
    market = pd.read_csv(MARKET_PATH)
    inflation = pd.read_csv(INFLATION_PATH)
    fuel = pd.read_csv(FUEL_PATH)
    fertilizer = pd.read_csv(FERTILIZER_PATH)
    planted = pd.read_csv(PLANTED_PATH)

    return market, inflation, fuel, fertilizer, planted


def prepare_market_data(market):
    market = market.copy()

    market = rename_if_exists(market, {
        "TARIH": "date",
        "URUN_ADI": "product_name",
        "ORTALAMA_FIYAT": "average_price",
        "YIL": "year",
        "SEZON": "season",
        "AY": "month",
    })

    if "date" in market.columns:
        market["date"] = pd.to_datetime(market["date"], errors="coerce")

    if "year" not in market.columns or market["year"].isna().all():
        market["year"] = market["date"].dt.year
    else:
        market["year"] = pd.to_numeric(market["year"], errors="coerce")

    if "month" not in market.columns or market["month"].isna().all():
        market["month"] = market["date"].dt.month
    else:
        market["month"] = pd.to_numeric(market["month"], errors="coerce")

    if "season" not in market.columns or market["season"].isna().all():
        market["season"] = market["month"].apply(get_season)
    else:
        market["season"] = market["season"].apply(normalize_season)

    # Aralık ayı bir sonraki yılın Winter sezonuna aittir.
    # Eğer temiz marketplace dosyasında bu düzeltme daha önce yapıldıysa tekrar uygulama.
    date_year = market["date"].dt.year if "date" in market.columns else pd.Series(pd.NA, index=market.index)
    needs_december_shift = (market["month"] == 12) & (market["year"] == date_year)
    market.loc[needs_december_shift, "year"] += 1

    market["product_name"] = market["product_name"].apply(standardize_product_name)
    market["average_price"] = pd.to_numeric(market["average_price"], errors="coerce")

    market = market[market["product_name"].isin(PRODUCTS)].copy()

    market = market.dropna(
        subset=["product_name", "year", "season", "average_price"]
    )
    market["year"] = market["year"].astype(int)

    market = (
        market
        .groupby(["product_name", "year", "season"], as_index=False)
        .agg(average_price=("average_price", "mean"))
    )

    return market


def prepare_fertilizer_data(fertilizer):
    fertilizer = fertilizer.copy()

    fertilizer = rename_if_exists(fertilizer, {
        "Year": "year",
        "YIL": "year",
        "Ortalama_Gubre_Maliyeti_Ton_TL": "fertilizer_price",
    })

    fertilizer["year"] = pd.to_numeric(fertilizer["year"], errors="coerce")
    fertilizer["fertilizer_price"] = pd.to_numeric(
        fertilizer["fertilizer_price"],
        errors="coerce"
    )

    fertilizer = fertilizer.dropna(subset=["year", "fertilizer_price"])
    fertilizer["year"] = fertilizer["year"].astype(int)

    return (
        fertilizer[["year", "fertilizer_price"]]
        .drop_duplicates(subset=["year"])
    )


def prepare_fuel_data(fuel):
    fuel = fuel.copy()

    fuel = rename_if_exists(fuel, {
        "Year": "year",
        "YIL": "year",
        "Season": "season",
        "SEZON": "season",
        "Diesel_Price": "fuel_price",
    })

    fuel["year"] = pd.to_numeric(fuel["year"], errors="coerce")
    fuel["fuel_price"] = pd.to_numeric(fuel["fuel_price"], errors="coerce")
    fuel["season"] = fuel["season"].apply(normalize_season)

    fuel = fuel.dropna(subset=["year", "season", "fuel_price"])
    fuel["year"] = fuel["year"].astype(int)

    return (
        fuel[["year", "season", "fuel_price"]]
        .drop_duplicates(subset=["year", "season"])
    )


def prepare_inflation_data(inflation):
    inflation = inflation.copy()

    inflation = rename_if_exists(inflation, {
        "Year": "year",
        "YIL": "year",
        "Season": "season",
        "SEZON": "season",
        "annual_inflation_pct": "annual_inflation",
    })

    inflation["year"] = pd.to_numeric(inflation["year"], errors="coerce")
    inflation["annual_inflation"] = pd.to_numeric(
        inflation["annual_inflation"],
        errors="coerce"
    )
    inflation["season"] = inflation["season"].apply(normalize_season)

    inflation = inflation.dropna(subset=["year", "season", "annual_inflation"])
    inflation["year"] = inflation["year"].astype(int)

    columns = ["year", "season", "annual_inflation"]

    if "inflation_index" in inflation.columns:
        columns.append("inflation_index")

    return (
        inflation[columns]
        .drop_duplicates(subset=["year", "season"])
    )


def prepare_planted_data(planted):
    planted = planted.copy()

    planted = rename_if_exists(planted, {
        "ProductName": "product_name",
        "URUN_ADI": "product_name",
        "Year": "year",
        "YIL": "year",
        "District": "district",
        "Ekilen Alan": "planted_area",
        "Üretim Miktarı": "production_amount",
        "Ãœretim MiktarÄ±": "production_amount",
    })

    planted["product_name"] = planted["product_name"].apply(standardize_product_name)
    planted["year"] = pd.to_numeric(planted["year"], errors="coerce")
    planted["planted_area"] = pd.to_numeric(planted["planted_area"], errors="coerce")
    planted["production_amount"] = pd.to_numeric(
        planted["production_amount"],
        errors="coerce"
    )

    planted = planted.dropna(
        subset=["product_name", "year", "planted_area", "production_amount"]
    )
    planted["year"] = planted["year"].astype(int)
    planted = planted[planted["product_name"].isin(PRODUCTS)].copy()

    # İlçe bazlı İzmir kayıtlarını ürün-yıl bazında il toplamına çevir.
    planted = (
        planted
        .groupby(["product_name", "year"], as_index=False)
        .agg(
            planted_area=("planted_area", "sum"),
            production_amount=("production_amount", "sum")
        )
    )

    return planted


def add_lag_features(market):
    market = market.copy()
    market["season_order"] = market["season"].map(SEASON_ORDER)

    market = (
        market
        .sort_values(["product_name", "year", "season_order"])
        .reset_index(drop=True)
    )

    market["lag_1_price"] = (
        market
        .groupby("product_name")["average_price"]
        .shift(1)
    )

    market["lag_4_price"] = (
        market
        .groupby("product_name")["average_price"]
        .shift(4)
    )

    return market.dropna(subset=["lag_1_price", "lag_4_price"])


def build_final_dataset():
    market, inflation, fuel, fertilizer, planted = load_data()

    market = prepare_market_data(market)
    fertilizer = prepare_fertilizer_data(fertilizer)
    fuel = prepare_fuel_data(fuel)
    inflation = prepare_inflation_data(inflation)
    planted = prepare_planted_data(planted)

    market = market.merge(fertilizer, on="year", how="left")
    market = market.merge(fuel, on=["year", "season"], how="left")
    market = market.merge(inflation, on=["year", "season"], how="left")
    market = market.merge(planted, on=["year", "product_name"], how="left")

    market = add_lag_features(market)

    drop_columns = [
        "season_order",
        "inflation_index",
    ]

    existing_drop_columns = [
        column for column in drop_columns
        if column in market.columns
    ]
    market = market.drop(columns=existing_drop_columns)

    market = market.drop_duplicates()

    required_columns = [
        "average_price",
        "fertilizer_price",
        "fuel_price",
        "annual_inflation",
        "planted_area",
        "production_amount",
        "lag_1_price",
        "lag_4_price",
    ]

    market = market.dropna(subset=required_columns)

    market = market[
        [
            "product_name",
            "year",
            "season",
            "average_price",
            "fertilizer_price",
            "fuel_price",
            "annual_inflation",
            "planted_area",
            "production_amount",
            "lag_1_price",
            "lag_4_price",
        ]
    ]

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    market.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    return market


if __name__ == "__main__":
    final_dataset = build_final_dataset()

    print("Final dataset oluşturuldu.")
    print("Satır sayısı:", len(final_dataset))
    print("Kolonlar:", list(final_dataset.columns))
    print(final_dataset.head(5))
