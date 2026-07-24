from pathlib import Path
import re

import pandas as pd
import pulp

from app.services.price_prediction import predict_products


DATAPATH = "data/processed/data_files/final_optimization.csv"
QUOTAPATH = "data/processed/data_files/cleaned_quota.csv"


def normalize_text(value):
    text = (
        str(value)
        .replace("İ", "I").replace("ı", "I")
        .replace("Ş", "S").replace("ş", "S")
        .replace("Ğ", "G").replace("ğ", "G")
        .replace("Ü", "U").replace("ü", "U")
        .replace("Ö", "O").replace("ö", "O")
        .replace("Ç", "C").replace("ç", "C")
        .upper().strip()
    )
    return re.sub(r"\s+", " ", text)


def normalize_product_name(value):
    text = normalize_text(value)
    text = text.replace("(", "").replace(")", "").replace(",", "").replace("-", " ")
    return re.sub(r"\s+", " ", text).strip()


def load_optimization_data():
    df = pd.read_csv(DATAPATH)
    quota = pd.read_csv(QUOTAPATH)

    df["district_key"] = df["district"].apply(normalize_text)
    df["product_key"] = df["product_name"].apply(normalize_product_name)

    quota["district_key"] = quota["district"].apply(normalize_text)
    quota["product_key"] = quota["product_name"].apply(normalize_product_name)

    quota["quota"] = pd.to_numeric(quota["quota"], errors="coerce")

    quota = quota.drop_duplicates(subset=["district_key", "product_key"])

    df = df.merge(
        quota[["district_key", "product_key", "quota"]],
        on=["district_key", "product_key"],
        how="left"
    )

    df = df.drop(columns=["district_key", "product_key"])

    return df


def get_suitable_products(df, district):
    data = df.copy()

    data["planted_area"] = pd.to_numeric(data["planted_area"], errors="coerce")
    data["production_amount"] = pd.to_numeric(data["production_amount"], errors="coerce")

    filtered_df = data[
        (data["district"] == district) &
        (data["planted_area"] > 0) &
        (data["production_amount"] > 0)
    ]

    return filtered_df.reset_index(drop=True)


def calculate_product_summary(valid_products_df):
    data = valid_products_df.copy()

    data["yield_per_decare"] = (
        data["production_amount"] * 1000 / data["planted_area"]
    )

    summary = (
        data.groupby(["district", "product_name"], as_index=False)
        .agg(
            average_yield_per_decare=("yield_per_decare", "mean"),
            quota=("quota", "first"),
        )
    )

    summary["average_yield_per_decare"] = (
        summary["average_yield_per_decare"].round(2)
    )
    summary["quota"] = pd.to_numeric(summary["quota"], errors="coerce")

    return summary.drop_duplicates().reset_index(drop=True)


def get_predicted_price_for_season(product_name, season):
    predictions = predict_products(product_name)

    for prediction in predictions:
        if prediction["season"] == season:
            return float(prediction["predicted_price"])

    raise ValueError(f"{product_name} icin {season} tahmini bulunamadi.")


def add_price_and_revenue(products, season):
    data = calculate_product_summary(products)

    predicted_prices = []

    for product_name in data["product_name"]:
        try:
            predicted_price = get_predicted_price_for_season(product_name, season)
        except ValueError:
            predicted_price = None

        predicted_prices.append(predicted_price)

    data["predicted_price"] = predicted_prices
    data = data[data["predicted_price"].notna()].reset_index(drop=True)

    data["revenue_per_decare"] = (
        data["average_yield_per_decare"] * data["predicted_price"]
    )

    return data


def estimated_revenue(products, area, season):
    data = add_price_and_revenue(products, season)
    data["estimated_revenue"] = data["revenue_per_decare"] * area

    return data


def safe_name(product_name):
    return re.sub(r"[^A-Za-z0-9_]", "_", product_name)


def create_planting_plan(
    district,
    season,
    total_area,
    selected_products=None,
    max_share=0.4,
):
    df = load_optimization_data()
    suitable_products = get_suitable_products(df, district)
    revenue_data = add_price_and_revenue(suitable_products, season)

    if selected_products:
        revenue_data = revenue_data[
            revenue_data["product_name"].isin(selected_products)
        ].reset_index(drop=True)

    if revenue_data.empty:
        raise ValueError("Bu il/ilce icin uygun urun bulunamadi.")

    model = pulp.LpProblem("optimal_ekim_plani", pulp.LpMaximize)

    area_vars = {}
    for _, row in revenue_data.iterrows():
        product_name = row["product_name"]

        area_vars[product_name] = pulp.LpVariable(
            name=f"x_{safe_name(product_name)}",
            lowBound=0,
            cat="Continuous"
        )

    model += pulp.lpSum(
        area_vars[row["product_name"]] * row["revenue_per_decare"]
        for _, row in revenue_data.iterrows()
    )

    model += (
        pulp.lpSum(area_vars.values()) == total_area,
        "total_area_constraint"
    )

    for _, row in revenue_data.iterrows():
        product_name = row["product_name"]

        model += (
            area_vars[product_name] <= total_area * max_share,
            f"max_share_{safe_name(product_name)}"
        )

        if pd.notna(row.get("quota")):
            model += (
                area_vars[product_name] <= row["quota"],
                f"quota_{safe_name(product_name)}"
            )

    status = model.solve(pulp.PULP_CBC_CMD(msg=False))

    if pulp.LpStatus[status] != "Optimal":
        raise ValueError(f"Optimal ekim plani bulunamadi: {pulp.LpStatus[status]}")

    result_rows = []

    for _, row in revenue_data.iterrows():
        product_name = row["product_name"]
        planted_area = area_vars[product_name].value()

        if planted_area is None or planted_area <= 0:
            continue

        estimated_production_kg = (
            planted_area * row["average_yield_per_decare"]
        )

        gross_revenue = (
            estimated_production_kg * row["predicted_price"]
        )

        result_rows.append({
            "district": district,
            "season": season,
            "product_name": product_name,
            "recommended_area": round(planted_area, 2),
            "average_yield_per_decare": row["average_yield_per_decare"],
            "estimated_production_kg": round(estimated_production_kg, 2),
            "predicted_price": row["predicted_price"],
            "gross_revenue": round(gross_revenue, 2),
        })

    result = pd.DataFrame(result_rows)

    result = result.sort_values(
        by="gross_revenue",
        ascending=False
    ).reset_index(drop=True)

    return result.to_dict(orient="records")


def create_plan_for_user_fields(
    fields,
    season,
    selected_products=None,
):
    all_plans = []

    for field in fields:
        field_id = field["id"]
        district = field["district"]
        total_area = field["area"]

        try:
            plan = create_planting_plan(
                district=district,
                season=season,
                total_area=total_area,
                selected_products=selected_products
            )

            all_plans.append({
                "field_id": field_id,
                "district": district,
                "total_area": total_area,
                "success": True,
                "plan": plan,
            })

        except ValueError as error:
            all_plans.append({
                "field_id": field_id,
                "district": district,
                "total_area": total_area,
                "success": False,
                "error": str(error),
                "plan": [],
            })

    return all_plans


if __name__ == "__main__":
    df = load_optimization_data()
    print("Veri yuklendi:")
    print(df.head())
    print(df.columns)
    print("Kota eslesen satir sayisi:", df["quota"].notna().sum())
    print("Kota bos kalan satir sayisi:", df["quota"].isna().sum())

    district = "Tire"
    season = "Winter"

    suitable = get_suitable_products(df, district)
    print("Uygun urunler:")
    print(suitable.nunique())

    summary = calculate_product_summary(suitable)
    print("Urun ozeti:")
    print(summary.head())

    revenue = add_price_and_revenue(suitable, season)
    print("Tahmini fiyat ve gelir:")
    print(revenue.head())

    plan = create_planting_plan(
        district=district,
        season=season,
        total_area=100,
        max_share=0.4
    )

    print("Optimizasyon sonucu:")
    for item in plan:
        print(item)