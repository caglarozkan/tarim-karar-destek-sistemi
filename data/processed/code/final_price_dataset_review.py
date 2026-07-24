import pandas as pd


MARKET_PATH = "data/processed/data_files/cleaned_all_marketplace.csv"
FERTILIZER_PATH = "data/processed/data_files/cleaned_fertilizer.csv"
FUEL_PATH = "data/processed/data_files/seasonal_fuel_prices.csv"
INFLATION_PATH = "data/processed/data_files/seasonal_inflation.csv"
TUIK_PATH = "data/processed/data_files/cleaned_tuik.csv"

OUTPUT_PATH = "data/processed/data_files/final_price_dataset.csv"


SEASON_ORDER = {
    "Winter": 1,
    "Spring": 2,
    "Summer": 3,
    "Fall": 4,
}


PRODUCT_NAME_MAP = {
    "DOMATES SALKIM": "DOMATES SALKIM",
    "DOMATES SOFRALIK": "DOMATES SALKIM",
    "SALATALIK SILOR": "SALATALIK SILOR",
    "HIYAR SOFRALIK": "SALATALIK SILOR",
    "KABAK SAKIZ": "KABAK TAZE",
    "KABAK TAZE": "KABAK TAZE",
    "KARPUZ": "KARPUZ",
    "SOGAN KURU": "SOGAN KURU",
    "SOĞAN KURU": "SOGAN KURU",
    "BIBER SIVRI": "BIBER SIVRI",
    "BİBER SİVRİ": "BIBER SIVRI",
    "PATLICAN": "PATLICAN UZUN",
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


ALLOWED_PRODUCTS = list(set(PRODUCT_NAME_MAP.values()))


def normalize_product_name(value):
    value = str(value).upper().strip()

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

    value = " ".join(value.split())

    return PRODUCT_NAME_MAP.get(value, value)


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


def prepare_market():
    market = pd.read_csv(
    MARKET_PATH,
    engine="python",
    on_bad_lines="skip"
)

    market = market.rename(columns={
        "TARIH": "date",
        "URUN_ADI": "product_name",
        "ORTALAMA_FIYAT": "average_price",
        "YIL": "year",
        "SEZON": "season",
        "AY": "month",
    })

    market["date"] = pd.to_datetime(market["date"], errors="coerce")

    if "year" not in market.columns:
        market["year"] = market["date"].dt.year
    else:
        market["year"] = pd.to_numeric(market["year"], errors="coerce")
        market.loc[market["year"].isna(), "year"] = market["date"].dt.year

    if "month" not in market.columns:
        market["month"] = market["date"].dt.month
    else:
        market["month"] = pd.to_numeric(market["month"], errors="coerce")
        market.loc[market["month"].isna(), "month"] = market["date"].dt.month

    market["season"] = market["month"].apply(get_season)
    market["product_name"] = market["product_name"].apply(normalize_product_name)

    market["average_price"] = pd.to_numeric(
        market["average_price"],
        errors="coerce"
    )

    market = market[
        market["product_name"].isin(ALLOWED_PRODUCTS)
    ]

    market = market[
        market["average_price"].notna()
        & market["year"].notna()
        & market["season"].notna()
    ]

    market = (
        market.groupby(
            ["product_name", "year", "season"],
            as_index=False
        )
        .agg(
            average_price=("average_price", "mean")
        )
    )

    market["average_price"] = market["average_price"].round(2)

    return market


def prepare_tuik():
    tuik = pd.read_csv(
    TUIK_PATH,
    engine="python",
    on_bad_lines="skip"
)

    tuik = tuik.rename(columns={
        "ProductName": "product_name",
        "Year": "year",
        "District": "district",
        "Ekilen Alan": "planted_area",
        "Üretim Miktarı": "production_amount",
    })

    tuik["product_name"] = tuik["product_name"].apply(normalize_product_name)
    tuik["year"] = pd.to_numeric(tuik["year"], errors="coerce")

    tuik["planted_area"] = pd.to_numeric(
        tuik["planted_area"],
        errors="coerce"
    )

    tuik["production_amount"] = pd.to_numeric(
        tuik["production_amount"],
        errors="coerce"
    )

    tuik = (
        tuik.groupby(
            ["product_name", "year"],
            as_index=False
        )
        .agg(
            planted_area=("planted_area", "sum"),
            production_amount=("production_amount", "sum")
        )
    )

    return tuik


def prepare_fertilizer():
    fertilizer = pd.read_csv(
    FERTILIZER_PATH,
    engine="python",
    on_bad_lines="skip"
)

    fertilizer = fertilizer.rename(columns={
        "YIL": "year",
        "Year": "year",
        "Ortalama_Gubre_Maliyeti_Ton_TL": "fertilizer_price",
    })

    fertilizer["year"] = pd.to_numeric(fertilizer["year"], errors="coerce")
    fertilizer["fertilizer_price"] = pd.to_numeric(
        fertilizer["fertilizer_price"],
        errors="coerce"
    )

    return fertilizer[["year", "fertilizer_price"]].drop_duplicates()


def prepare_fuel():
    fuel = pd.read_csv(
    FUEL_PATH,
    engine="python",
    on_bad_lines="skip"
)

    fuel = fuel.rename(columns={
        "diesel_price": "fuel_price",
        "FUEL_PRICE": "fuel_price",
        "Year": "year",
        "YIL": "year",
        "SEZON": "season",
    })

    fuel["year"] = pd.to_numeric(fuel["year"], errors="coerce")
    fuel["fuel_price"] = pd.to_numeric(fuel["fuel_price"], errors="coerce")

    return fuel[["year", "season", "fuel_price"]].drop_duplicates()


def prepare_inflation():
    inflation = pd.read_csv(
    INFLATION_PATH,
    engine="python",
    on_bad_lines="skip"
)

    inflation = inflation.rename(columns={
        "YIL": "year",
        "Year": "year",
        "annual_inflation": "annual_inflation",
        "Annual_Inflation": "annual_inflation",
    })

    inflation["year"] = pd.to_numeric(inflation["year"], errors="coerce")
    inflation["annual_inflation"] = pd.to_numeric(
        inflation["annual_inflation"],
        errors="coerce"
    )

    return inflation[["year", "annual_inflation"]].drop_duplicates()


market = prepare_market()
tuik = prepare_tuik()
fertilizer = prepare_fertilizer()
fuel = prepare_fuel()
inflation = prepare_inflation()

final = market.merge(
    fertilizer,
    on="year",
    how="left"
)

final = final.merge(
    fuel,
    on=["year", "season"],
    how="left"
)

final = final.merge(
    inflation,
    on="year",
    how="left"
)

final = final.merge(
    tuik,
    on=["product_name", "year"],
    how="left"
)

final["season_order"] = final["season"].map(SEASON_ORDER)

final = final.sort_values(
    ["product_name", "year", "season_order"]
).reset_index(drop=True)

final["lag_1_price"] = (
    final.groupby("product_name")["average_price"]
    .shift(1)
)

final["lag_4_price"] = (
    final.groupby("product_name")["average_price"]
    .shift(4)
)

final["lag_1_price"] = final["lag_1_price"].fillna(
    final["average_price"]
)

final["lag_4_price"] = final["lag_4_price"].fillna(
    final["lag_1_price"]
)

final = final.drop(columns=["season_order"])

final = final[
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

final.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("final_price_dataset.csv oluşturuldu.")
print(final.head(20))