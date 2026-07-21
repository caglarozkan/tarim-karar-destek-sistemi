import pandas as pd

market = pd.read_csv("data/processed/data_files/cleaned_all_marketplace.csv")
tuik = pd.read_csv("data/processed/data_files/cleaned_tuik.csv")


seasonal_market = (
    market.groupby(
        ["product_name", "year", "season"],
        as_index=False
    )
    .agg(
        average_price=("average_price", "mean"),
        min_price=("min_price", "mean"),
        max_price=("max_price", "mean")
    )
)

seasonal_market["average_price"] = (
    seasonal_market["average_price"].round(2)
)

seasons = pd.DataFrame({
    "season": ["Winter", "Spring", "Summer", "Fall"]
})

tuik_seasonal = (
    tuik.assign(key=1)
        .merge(seasons.assign(key=1), on="key")
        .drop(columns="key")
)
final_df = tuik_seasonal.merge(
    seasonal_market,
    on=["product_name", "year", "season"],
    how="left"
)
final_df["province"] = (
    final_df["district"]
    .str.extract(r"^([^(]+)")
    .iloc[:, 0]
    .str.strip()
)

final_df["district"] = (
    final_df["district"]
    .str.extract(r"\((.*?)\)")
    .iloc[:, 0]
    .str.strip()
)
final_df = final_df[
    [
        "province",
        "district",
        "product_name",
        "year",
        "season",
        "planted_area",
        "production_amount",
        "average_price",
        "min_price",
        "max_price"
    ]
]
    
final_df = final_df[final_df["planted_area"] != 0]
final_df["yield_per_decare_kg"] = (
        final_df["production_amount"] *1000/ final_df["planted_area"]
    )

final_df = final_df[
        final_df["yield_per_decare_kg"].notna()
        & (final_df["yield_per_decare_kg"] > 0)
    ]
final_df=final_df.replace({"SALATALIK SİLOR":"SALATALIK SILOR"})
final_df=final_df.drop(columns={"average_price","min_price","max_price"})
final_df.to_csv("data/processed/data_files/final_optimization.csv")