import pandas as pd

TUIK_PATH = "data/processed/data_files/cleaned_tuik.csv"
FERTILIZER_PATH = "data/processed/data_files/cleaned_fertilizer.csv"
FUEL_PATH = "data/processed/data_files/seasonal_fuel_prices.csv"
MARKET_PATH = "data/processed/data_files/final_price_dataset.csv"
OUTPUT_PATH = "data/processed/data_files/final_risk_dataset.csv"


tuik = pd.read_csv(TUIK_PATH)
gubre = pd.read_csv(FERTILIZER_PATH)
petrol = pd.read_csv(FUEL_PATH)
market = pd.read_csv(MARKET_PATH)

tuik.columns = tuik.columns.str.strip()
gubre.columns = gubre.columns.str.strip()
petrol.columns = petrol.columns.str.strip()
market.columns = market.columns.str.strip()


for df in [tuik, gubre, petrol, market]:
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df.dropna(subset=["year"], inplace=True)
    df["year"] = df["year"].astype(int)

tuik["planted_area"] = pd.to_numeric(tuik["planted_area"], errors="coerce")
tuik["production_amount"] = pd.to_numeric(tuik["production_amount"], errors="coerce")
petrol["diesel_price"] = pd.to_numeric(petrol["diesel_price"], errors="coerce")

if "fertilizer_price" in gubre.columns:
    gubre["fertilizer_price"] = pd.to_numeric(gubre["fertilizer_price"], errors="coerce")

if "average_price" in market.columns:
    market["average_price"] = pd.to_numeric(market["average_price"], errors="coerce")


seasons = pd.DataFrame({
    "season": ["Winter", "Spring", "Summer", "Fall"]
})

tuik_seasonal = (
    tuik.assign(key=1)
    .merge(seasons.assign(key=1), on="key")
    .drop(columns="key")
)

market_price = (
    market.groupby(["product_name", "year", "season"], as_index=False)
    .agg(average_price=("average_price", "mean"))
)

final = tuik_seasonal.merge(
    petrol[["year", "season", "diesel_price"]],
    on=["year", "season"],
    how="left"
)

final = final.merge(
    gubre,
    on="year",
    how="left"
)

final = final.merge(
    market_price,
    on=["product_name", "year", "season"],
    how="left"
)

final = final[
    (final["year"] != 2013) &
    (final["planted_area"] > 0) &
    (final["production_amount"] > 0)
].copy()

final["yield_per_decare_kg"] = (
    final["production_amount"] * 1000 / final["planted_area"]
)

drop_columns = [
    "Amonyum_Sulfat",
    "CAN",
    "Ure",
    "DAP",
    "Gubre_20_20_0",
    "unit",
    "date",
    "product_type",
    "min_price",
    "max_price",
    "month"
]

final = final.drop(
    columns=[col for col in drop_columns if col in final.columns]
)

final = final.drop_duplicates().reset_index(drop=True)

final["average_price"] = final["average_price"].fillna(
    final.groupby(["product_name", "year"])["average_price"]
    .transform("mean")
)

final["average_price"] = final["average_price"].fillna(
    final.groupby(["product_name"])["average_price"]
    .transform("mean")
)

final["average_price"] = final["average_price"].fillna(
    final["average_price"].mean()
)
final.to_csv(
    OUTPUT_PATH,
    index=False,
    encoding="utf-8-sig"
)

print("final_risk_dataset.csv olusturuldu.")
print(final.head())
print(final["average_price"].isna().sum())