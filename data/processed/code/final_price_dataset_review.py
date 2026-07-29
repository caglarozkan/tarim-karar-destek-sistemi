import pandas as pd


MARKET_PATH = "data/processed/data_files/cleaned_all_marketplace.csv"
FERTILIZER_PATH = "data/processed/data_files/cleaned_fertilizer.csv"
FUEL_PATH = "data/processed/data_files/seasonal_fuel_prices.csv"
INFLATION_PATH = "data/processed/data_files/seasonal_inflation.csv"
TUIK_PATH = "data/processed/data_files/cleaned_tuik.csv"
PRODUCTION_PATH="data/processed/data_files/üretim_miktari_sonuclari.csv"
PLANTED_PATH="data/processed/data_files/cleaned_quota.csv"

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
    market["min_price"] = pd.to_numeric(market["min_price"], errors="coerce")
    market["max_price"] = pd.to_numeric(market["max_price"], errors="coerce")
    
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
            average_price=("average_price", "mean"),
            min_price=("min_price","mean"),
            max_price=("max_price","mean")
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

    inflation["year"] = pd.to_numeric(inflation["year"], errors="coerce")
    inflation["annual_inflation"] = pd.to_numeric(
        inflation["annual_inflation"],
        errors="coerce"
    )

    return inflation[["year","season", "annual_inflation"]].drop_duplicates()


def add_lag_features(final):
    final = final.copy()
    final["season_order"] = final["season"].map(SEASON_ORDER)

    # 1) Her urun icin olasi TUM yil x sezon kombinasyonlarini iceren
    #    tam bir izgara olustur (eksik sezonlar da satir olarak var olsun)
    all_products = final["product_name"].unique()
    all_years = final["year"].unique()
    all_seasons = list(SEASON_ORDER.keys())

    full_index = pd.MultiIndex.from_product(
        [all_products, all_years, all_seasons],
        names=["product_name", "year", "season"],
    )
    grid = pd.DataFrame(index=full_index).reset_index()
    grid["season_order"] = grid["season"].map(SEASON_ORDER)

    # 2) Gercek veriyi bu tam izgaraya birlestir; eksik yil-sezon
    #    kombinasyonlari icin average_price NaN olur
    merged = grid.merge(
        final[["product_name", "year", "season", "average_price"]],
        on=["product_name", "year", "season"],
        how="left",
    )

    merged = merged.sort_values(
        ["product_name", "year", "season_order"]
    ).reset_index(drop=True)

    # 3) Artik shift, gercek kronolojik bir onceki/4 onceki sezonu veriyor.
    #    Eksik bir sezon araya girdiyse, sonraki sezonun lag'i otomatik NaN olur.
    merged["lag_1_price"] = merged.groupby("product_name")["average_price"].shift(1)
    merged["lag_4_price"] = merged.groupby("product_name")["average_price"].shift(4)

    # 4) Sadece gercekte veride olan satirlari geri al (sentetik satirlari at)
    final = final.merge(
        merged[["product_name", "year", "season", "lag_1_price", "lag_4_price"]],
        on=["product_name", "year", "season"],
        how="left",
    )

    final = final.drop(columns=["season_order"])

    return final


def fill_2026_production(final):
    predicted = pd.read_csv(PRODUCTION_PATH)

    predicted = predicted.rename(columns={
        "2026 Üretim Miktari": "predicted_production_amount",
    })

    predicted["year"] = 2026
    predicted["product_name"] = predicted["product_name"].apply(normalize_product_name)

    predicted["predicted_production_amount"] = pd.to_numeric(
        predicted["predicted_production_amount"],
        errors="coerce",
    )

    predicted = (
        predicted
        .groupby(["year", "product_name"], as_index=False)["predicted_production_amount"]
        .sum()
    )

    final = final.merge(
        predicted,
        on=["year", "product_name"],
        how="left",
    )

    mask = (
        (final["year"] == 2026)
        & (final["production_amount"].isna())
        & (final["predicted_production_amount"].notna())
    )

    final.loc[mask, "production_amount"] = (
        final.loc[mask, "predicted_production_amount"].round(2)
    )

    return final.drop(columns=["predicted_production_amount"])


def fill_2026_planted_area(final):
    predicted = pd.read_csv(PLANTED_PATH)

    predicted = predicted.rename(columns={
        "quota": "predicted_planted_area",
        "2026 Ekim Miktarı": "predicted_planted_area",
        "2026 Ekim Miktari": "predicted_planted_area",
    })

    predicted["year"] = 2026
    predicted["product_name"] = predicted["product_name"].apply(normalize_product_name)

    predicted["predicted_planted_area"] = pd.to_numeric(
        predicted["predicted_planted_area"],
        errors="coerce",
    )

    predicted = (
        predicted
        .groupby(["year", "product_name"], as_index=False)["predicted_planted_area"]
        .sum()
    )

    final = final.merge(
        predicted,
        on=["year", "product_name"],
        how="left",
    )

    mask = (
        (final["year"] == 2026)
        & (final["planted_area"].isna())
        & (final["predicted_planted_area"].notna())
    )

    final.loc[mask, "planted_area"] = (
        final.loc[mask, "predicted_planted_area"].round(2)
    )

    return final.drop(columns=["predicted_planted_area"])


market = prepare_market()
tuik = prepare_tuik()
fertilizer = prepare_fertilizer()
fuel = prepare_fuel()
inflation = prepare_inflation()

final = market.merge(
    fertilizer,
    on="year",
    how="left",
)

final = final.merge(
    fuel,
    on=["year", "season"],
    how="left",
)

final = final.merge(
    inflation,
    on=["year", "season"],
    how="left",
)

final = final.merge(
    tuik,
    on=["product_name", "year"],
    how="left",
)

final = add_lag_features(final)

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
        "min_price",
        "max_price",
        "lag_1_price",
        "lag_4_price",
    ]
]

final = fill_2026_production(final)
final = fill_2026_planted_area(final)
 
final["season_order"] = final["season"].map(SEASON_ORDER)
final = final.sort_values(
    ["product_name", "year", "season_order"]
).reset_index(drop=True)
final = final.drop(columns=["season_order"])

final.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig",
)

print(final.sample(10))
print(final.isnull().sum())