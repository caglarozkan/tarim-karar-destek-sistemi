from pathlib import Path
import pulp
import pandas as pd
from price_prediction import predict_products

DATAPATH = "data/processed/data_files/final_optimization.csv"
QUOTAPATH="data/processed/data_files/cleaned_quota.csv"

df = pd.read_csv(DATAPATH)
quota=pd.read_csv(QUOTAPATH)

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

    summary =(
        data.groupby(
            ["province", "district", "product_name"],
            as_index=False
        )
        .agg(
            average_yield_per_decare=("yield_per_decare", "mean"),
        )
    )
    summary["average_yield_per_decare"] = (
        summary["average_yield_per_decare"].round(2)
    )
    summary = summary.drop_duplicates().reset_index(drop=True)

    return summary


def estimated_revenue(products,area):
    data = calculate_product_summary(products)
    predicted_prices = []

    for product_name in data["product_name"]:
        try:
            predicted_price = predict_products(product_name)
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

def add_price_and_revenue(products,season):
    data = calculate_product_summary(products)

    predicted_prices = []

    for product_name in data["product_name"]:
        try:
            predicted_price = predict_products(product_name, season)
        except ValueError:
            predicted_price = None

        predicted_prices.append(predicted_price)

    data["predicted_price"] = predicted_prices

    data = data[data["predicted_price"].notna()].reset_index(drop=True)

    data["revenue_per_decare"] = (
        data["average_yield_per_decare"] * data["predicted_price"]
    )

    return data


def create_planting_plan(
    df,
    district,
    season,
    total_area,
    selected_products=None
):
    suitable_products = get_suitable_products(df, district)

    revenue_data = add_price_and_revenue(suitable_products, season)

    if selected_products:
        revenue_data = revenue_data[
            revenue_data["product_name"].isin(selected_products)
        ].reset_index(drop=True)

    if revenue_data.empty:
        raise ValueError("Bu il/ilçe ve ürün seçimi için uygun ürün bulunamadı.")

    model=pulp.LpProblem("optimal_ekim_plani",pulp.LpMaximize)
    
    area_vars = {}
    for _, row in revenue_data.iterrows():
        product_name = row["product_name"]

        area_vars[product_name] = pulp.LpVariable(
            name=f"x_{product_name}",
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
            area_vars[product_name] <= total_area * 0.40,
            f"max_share_{product_name}"
        )

        if "quota" in revenue_data.columns and pd.notna(row.get("quota")):
            model += (
                area_vars[product_name] <= row["quota"],
                f"quota_{product_name}"
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

    return result



if __name__ == "__main__":
    district = input("Ilce giriniz: ")
    season = input("Sezon giriniz Winter/Spring/Summer/Fall: ")
    total_area = float(input("Toplam donum giriniz: "))

    product_input = input(
        "Ekmek istediginiz urunleri virgulle yazin. Sisteme birakmak icin bos birakin: "
    )

    if product_input.strip():
        selected_products = [
            product.strip().upper()
            for product in product_input.split(",")
        ]
    else:
        selected_products = None

    plan = create_planting_plan(
        df=df,
        district=district,
        season=season,
        total_area=total_area,
        selected_products=selected_products
    )

    print("\nOptimal ekim plani:")
    print(plan)