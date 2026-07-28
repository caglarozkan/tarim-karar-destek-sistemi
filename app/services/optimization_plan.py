from pathlib import Path
import re
from typing import Any
from datetime import date
import pandas as pd
import pulp
from app.services.fertilizer_service import get_commodity_price
from app.services.fuel_service import predict_fuel_price
from app.services.price_prediction import predict_product_price
from app.services.profit_service import kar_hesapla_tam


ROOT_DIR = Path(__file__).resolve().parent.parent.parent

DATAPATH = ROOT_DIR / "data" / "processed" / "data_files" / "final_optimization.csv"
QUOTAPATH = ROOT_DIR / "data" / "processed" / "data_files" / "cleaned_quota.csv"
YIELD_PATH=ROOT_DIR / "data" / "processed" / "data_files" / "predict_yield_per_decare.csv"
FERTILIZER_COMMODITY = "urea"

PRODUCT_SEASONS = {
    "DOMATES SALKIM": ["Spring"],
    "SALATALIK SILOR": ["Spring", "Summer"],
    "BEZELYE": ["Fall", "Winter"],
    "BAKLA": ["Fall", "Winter"],
    "KARNABAHAR": ["Summer", "Fall"],
    "LAHANA KIRMIZI": ["Summer", "Fall"],
    "LAHANA BEYAZ": ["Summer", "Fall"],
    "BROKOLI": ["Summer", "Fall"],
    "MARUL GOBEKLI": ["Fall", "Winter", "Spring"],
    "ISPANAK": ["Fall", "Winter"],
    "PIRASA": ["Spring", "Summer"],
    "BIBER SIVRI": ["Spring"],
    "KARPUZ": ["Spring"],
    "SOGAN KURU": ["Fall", "Spring"],
    "KABAK TAZE": ["Spring", "Summer"],
    "PATLICAN UZUN": ["Spring"],
}

def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_]", "_", str(value))


def load_optimization_data():
    df = pd.read_csv(DATAPATH)
    quota = pd.read_csv(QUOTAPATH)

    quota["quota"] = pd.to_numeric(quota["quota"], errors="coerce")
    quota = quota.drop_duplicates(subset=["district", "product_name"])

    return df.merge(
        quota[["district", "product_name", "quota"]],
        on=["district", "product_name"],
        how="left",
    )


def get_suitable_products(df, district, season=None):
    data = df.copy()

    data["planted_area"] = pd.to_numeric(data["planted_area"], errors="coerce")
    data["production_amount"] = pd.to_numeric(data["production_amount"], errors="coerce")

    mask = (
        (data["district"] == district)
        & (data["planted_area"] > 0)
        & (data["production_amount"] > 0)
    )

    if season:
        data["suitable_season"] = data["product_name"].map(PRODUCT_SEASONS)
        season_mask = data["suitable_season"].apply(
            lambda seasons: (
                season in seasons
                if isinstance(seasons, list)
                else False
            )
        )
        mask = mask & season_mask

    return (
        data[mask]
        .drop(columns=["suitable_season"], errors="ignore")
        .reset_index(drop=True)
    )

def calculate_product_summary(valid_products_df):
    data = valid_products_df.copy()
    production=pd.read_csv(YIELD_PATH)
    data["yield_per_decare_kg"] = production["predicted_yield_per_decare_kg"]

    summary = (
        data.groupby(["district", "product_name"], as_index=False)
        .agg(
            average_yield_per_decare=("yield_per_decare_kg", "mean"),
            quota=("quota", "first"),
        )
    )
    summary["average_yield_per_decare"] = summary["average_yield_per_decare"].round(2)
    summary["quota"] = pd.to_numeric(summary["quota"], errors="coerce")
    summary=summary.drop_duplicates().reset_index(drop=True)
    
    return summary

def get_fuel_price(target_year, target_season):
    return float(
        predict_fuel_price(target_year,target_season,))

def get_fertilizer_price():
    return float(get_commodity_price(FERTILIZER_COMMODITY))

def get_predicted_price(product_name, target_year, target_season):
    prediction = predict_product_price(
        product_name=product_name,
        target_year=target_year,
        target_season=target_season,
    )
    return float(prediction["predicted_price"])


def add_other_predictions(products, target_year, season):
    data = calculate_product_summary(products)

    if data.empty:
        return data

    try:
        fuel_price = get_fuel_price(target_year, season)
    except Exception:
        fuel_price = None

    try:
        fertilizer_price = get_fertilizer_price()
    except Exception:
        fertilizer_price = None

    predicted_prices = []

    for product_name in data["product_name"]:
        try:
            predicted_price = get_predicted_price(
                product_name=product_name,
                target_year=target_year,
                target_season=season,
            )
        except Exception:
            predicted_price = None

        predicted_prices.append(predicted_price)

    data["predicted_price"] = predicted_prices

    data = data[data["predicted_price"].notna()].reset_index(drop=True)

    if data.empty:
        return data

    data["predicted_price"] = pd.to_numeric(
        data["predicted_price"],
        errors="coerce",
    )

    data = data[data["predicted_price"].notna()].reset_index(drop=True)

    data["predicted_fuel_price"] = fuel_price
    data["current_fertilizer_price"] = fertilizer_price

    data["revenue_per_decare"] = (
        data["average_yield_per_decare"] * data["predicted_price"]
    )

    return data

def get_target_year(season):
    season_order = {
        "Winter": 1,
        "Spring": 2,
        "Summer": 3,
        "Fall": 4,
    }

    month_to_season = {
        12: "Winter",
        1: "Winter",
        2: "Winter",
        3: "Spring",
        4: "Spring",
        5: "Spring",
        6: "Summer",
        7: "Summer",
        8: "Summer",
        9: "Fall",
        10: "Fall",
        11: "Fall",
    }

    today = date.today()
    current_year = today.year
    current_month = today.month
    current_season = month_to_season[current_month]

    if season not in season_order:
        raise ValueError(f"Geçersiz sezon: {season}")

    if season_order[season] > season_order[current_season]:
        return current_year

    return current_year + 1
    
def filter_selected_products(data, selected_products):
    if not selected_products:
        return data

    return data[data["product_name"].isin(selected_products)].reset_index(drop=True)


def create_planting(
    district,
    season,
    total_area,
    selected_products=None,
    max_share=0.4,
):
    target_year=get_target_year(season)
    df = load_optimization_data()
    suitable_products = get_suitable_products(df, district, season=season)
    revenue_data = add_other_predictions(
        suitable_products,
        target_year=target_year,
        season=season,
    )
    revenue_data = filter_selected_products(revenue_data, selected_products)

    if revenue_data.empty:
        raise ValueError("Bu il/ilce icin uygun urun bulunamadi.")

    model = pulp.LpProblem("optimal_ekim_plani", pulp.LpMaximize)

    area_vars = {}
    for _, row in revenue_data.iterrows():
        product_name = row["product_name"]
        area_vars[product_name] = pulp.LpVariable(
            name=f"x_{safe_name(product_name)}",
            lowBound=0,
            cat="Continuous",
        )

    model += pulp.lpSum(
        area_vars[row["product_name"]] * row["revenue_per_decare"]
        for _, row in revenue_data.iterrows()
    )

    model += (
        pulp.lpSum(area_vars.values()) <= total_area,
        "total_area_constraint",
    )

    for _, row in revenue_data.iterrows():
        product_name = row["product_name"]

        model += (
            area_vars[product_name] <= total_area * max_share,
            f"max_share_{safe_name(product_name)}",
        )
        
        if pd.notna(row.get("quota")):
          model += (
            area_vars[product_name] <= row["quota"],
            f"quota_{safe_name(product_name)}",
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

        estimated_production_kg = planted_area * row["average_yield_per_decare"]
        gross_revenue = estimated_production_kg * row["predicted_price"]

        result_rows.append(
            {
                "district": district,
                "target_year": target_year,
                "season": season,
                "product_name": product_name,
                "recommended_area": round(planted_area, 2),
                "average_yield_per_decare": row["average_yield_per_decare"],
                "estimated_production_kg": round(estimated_production_kg, 2),
                "quota": None if pd.isna(row.get("quota")) else float(row["quota"]),
                "predicted_price": round(float(row["predicted_price"]), 2),
                "predicted_fuel_price": round(float(row["predicted_fuel_price"]), 2),
                "current_fertilizer_price": round(float(row["current_fertilizer_price"]), 2),
                "gross_revenue": round(gross_revenue, 2),
            }
        )

    result = pd.DataFrame(result_rows)
    result = result.sort_values(by="gross_revenue", ascending=False).reset_index(drop=True)

    return result.to_dict(orient="records")

def get_profi():
    profit=kar_hesapla_tam()
def create_plan_for_user_fields(
    fields,
    season,
    selected_products=None,
):
    all_plans = []
    target_year=get_target_year(season)
    for field in fields:
        field_id = field["id"]
        district = field["district"]
        total_area = field["area"]

        try:
            plan = create_planting(
                district=district,
                season=season,
                target_year=target_year,
                total_area=total_area,
                selected_products=selected_products,
            )

            all_plans.append(
                {
                    "field_id": field_id,
                    "district": district,
                    "total_area": total_area,
                    "target_year": target_year,
                    "success": True,
                    "plan": plan,
                }
            )

        except ValueError as error:
            all_plans.append(
                {
                    "field_id": field_id,
                    "district": district,
                    "total_area": total_area,
                    "target_year": target_year,
                    "success": False,
                    "error": str(error),
                    "plan": [],
                }
            )

