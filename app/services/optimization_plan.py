from pathlib import Path
import pulp
import pandas as pd
from price_prediction import predict_products

DATAPATH = "data/processed/data_files/final_optimization.csv"

df = pd.read_csv(DATAPATH)

def get_suitable_products(df, province, district):
    data = df.copy()

    data["planted_area"] = pd.to_numeric(data["planted_area"], errors="coerce")
    data["production_amount"] = pd.to_numeric(data["production_amount"], errors="coerce")

    filtered_df = data[
        (data["province"] == province) &
        (data["district"] == district) &
        (data["planted_area"] > 0) &
        (data["production_amount"] > 0)
    ]

    return filtered_df.reset_index(drop=True)


def calculate_product_summary(valid_products_df, season=None):
    data = valid_products_df.copy()

    if season is not None:
        data = data[data["season"] == season]

    data["yield_per_decare"] = (
        data["production_amount"] * 1000 / data["planted_area"]
    )

    summary = (
        data.groupby(
            ["province", "district", "product_name", "season"],
            as_index=False
        )
        .agg(
            total_planted_area=("planted_area", "sum"),
            total_production_amount=("production_amount", "sum"),
            average_yield_per_decare=("yield_per_decare", "mean"),
            quota_2026=("quota_2026", "first")

        )
    )

    summary["average_yield_per_decare"] = (
        summary["average_yield_per_decare"].round(2)
    )

    summary = summary.drop_duplicates().reset_index(drop=True)

    return summary


def estimated_revenue(products, season, area):
    data = calculate_product_summary(products, season)

    predicted_prices = []

    for product_name in data["product_name"]:
        try:
            predicted_price = predict_products(product_name, season)
        except ValueError:
            predicted_price = None

        predicted_prices.append(predicted_price)

    data["predicted_price"] = predicted_prices

    data = data[data["predicted_price"].notna()].reset_index(drop=True)

    data["estimated_revenue"] = (
        data["average_yield_per_decare"] *
        data["predicted_price"] *
        area
    )

    return data


a = get_suitable_products(df, "İzmir", "Bayındır")

for season in ("Winter", "Spring", "Fall"):
    b = estimated_revenue(a, season, 10)
    print(season)
    print(b)