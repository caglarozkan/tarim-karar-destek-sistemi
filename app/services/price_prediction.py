from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any
import numpy as np
import joblib
import pandas as pd

from catboost import CatBoostRegressor

from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split

from app.services.fertilizer_service import get_commodity_price
from app.services.fuel_service import predict_fuel_price
from app.services.inflation_service import predict_inflation


DATASET_PATH = Path("data/processed/data_files/final_price_dataset.csv")
MODEL_PATH = Path("models/price_model_catboost.pkl")

TARGET_COLUMN = "average_price"

CATEGORICAL_FEATURES = ["product_name", "season","product_season","season_year"]

NUMERIC_FEATURES = [
    "year",
    "fertilizer_price",
    "fuel_price",
    "annual_inflation",
    "planted_area",
    "production_amount",
    "lag_1_price",
    "lag_4_price",
    "lag_8_price",
    "same_season_growth",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES

SEASON_ORDER = {
    "Winter": 1,
    "Spring": 2,
    "Summer": 3,
    "Fall": 4,
}

SEASON_SEQUENCE = ["Winter", "Spring", "Summer", "Fall"]


def validate_season(season: str) -> str:
    season = str(season).strip()

    if season not in SEASON_ORDER:
        valid_seasons = ", ".join(SEASON_SEQUENCE)
        raise ValueError(
            f"Gecersiz sezon: {season}. Gecerli sezonlar: {valid_seasons}"
        )

    return season


def season_sort_value(season: str) -> int:
    season = validate_season(season)
    return SEASON_ORDER[season]


def get_current_season(today: date | None = None) -> tuple[int, str]:
    if today is None:
        today = date.today()

    year = today.year
    month = today.month

    if month in [12, 1, 2]:
        return year, "Winter"
    if month in [3, 4, 5]:
        return year, "Spring"
    if month in [6, 7, 8]:
        return year, "Summer"

    return year, "Fall"


def get_target_year(target_season: str, today: date | None = None) -> int:
    if today is None:
        today = date.today()

    target_season = validate_season(target_season)
    current_year, current_season = get_current_season(today)

    if SEASON_ORDER[target_season] > SEASON_ORDER[current_season]:
        return current_year

    return current_year + 1


def load_dataset(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Dataset bulunamadi: {dataset_path}")

    df = pd.read_csv(dataset_path)

    df["product_season"] = (
    df["product_name"].astype(str) + "_" + df["season"].astype(str)
)

    df["season_year"] = (
    df["season"].astype(str) + "_" + df["year"].astype(str))
    df["lag_8_price"] = (
    df.groupby("product_name")[TARGET_COLUMN]
    .shift(8)
)   
    df["same_season_growth"] = np.where(
    df["lag_8_price"] > 0,
    (df["lag_4_price"] - df["lag_8_price"]) / df["lag_8_price"],
    np.nan,
) 
    
    df["same_season_growth"] = df.groupby("product_name")["same_season_growth"].transform(
    lambda series: series.fillna(series.median())
)

    df["same_season_growth"] = df["same_season_growth"].fillna(
    df["same_season_growth"].median()
)
    df = df.dropna(subset=[
    "lag_1_price",
    "lag_4_price",
])
    required_columns = [TARGET_COLUMN, *FEATURE_COLUMNS]
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Dataset eksik kolon iceriyor: {missing_columns}")

    df["product_name"] = df["product_name"].astype(str)
    df["season"] = df["season"].astype(str).apply(validate_season)

    for column in NUMERIC_FEATURES + [TARGET_COLUMN]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=[TARGET_COLUMN, *FEATURE_COLUMNS])
    df["year"] = df["year"].astype(int)

    return df


def build_price_model() -> CatBoostRegressor:
    return CatBoostRegressor(
        iterations=700,
        learning_rate=0.03,
        depth=6,
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
    )


def get_cat_feature_indices() -> list[int]:
    return [
        FEATURE_COLUMNS.index(column)
        for column in CATEGORICAL_FEATURES
    ]


def train_price_model(
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
) -> dict[str, float]:
    df = load_dataset(dataset_path)

    x = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
    )

    model = build_price_model()

    model.fit(
        x_train,
        y_train,
        cat_features=get_cat_feature_indices(),
    )

    predictions = model.predict(x_test)
    predictions = [max(0.0, float(p)) for p in predictions]

    metrics = {
        "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
        "rmse": round(float(root_mean_squared_error(y_test, predictions)), 4),
        "mape": round(
            float(mean_absolute_percentage_error(y_test, predictions) * 100),
            2,
        ),
        "r2": round(float(r2_score(y_test, predictions)), 4)
        if len(y_test) > 1
        else 0.0,
        "row_count": float(len(df)),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    return metrics


def load_or_train_model(
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
) -> CatBoostRegressor:
    if not Path(model_path).exists():
        train_price_model(
            dataset_path=dataset_path,
            model_path=model_path,
        )

    return joblib.load(model_path)


def get_product_history(df: pd.DataFrame, product_name: str) -> pd.DataFrame:
    product_df = df[
        df["product_name"].astype(str).str.lower() == product_name.lower()
    ].copy()

    if product_df.empty:
        raise ValueError(f"{product_name} icin gecmis fiyat verisi bulunamadi.")

    product_df["_season_order"] = product_df["season"].map(season_sort_value)

    return product_df.sort_values(
        ["year", "_season_order"]
    ).reset_index(drop=True)
    
def get_lag_prices(product_history: pd.DataFrame) -> tuple[float, float, float]:
    history = product_history.sort_values(["year", "_season_order"]).copy()

    prices = history["average_price"].dropna().tolist()

    if not prices:
        raise ValueError("Bu ürün için geçmiş fiyat bilgisi bulunamadı.")

    lag_1_price = prices[-1]
    lag_4_price = prices[-4] if len(prices) >= 4 else lag_1_price
    lag_8_price = prices[-8] if len(prices) >= 8 else lag_4_price

    return lag_1_price, lag_4_price, lag_8_price
def latest_or_given(
    product_history: pd.DataFrame,
    column: str,
    value: float | None,
) -> float:
    if value is not None:
        return float(value)

    return float(product_history.iloc[-1][column])


def get_fuel_for_period(target_year: int, target_season: str) -> float:
    return float(predict_fuel_price(target_year, target_season))


def get_inflation_for_period(target_year: int, target_season: str) -> float:
    return float(predict_inflation(target_year, target_season))


def build_prediction_input(
    product_name: str,
    product_history: pd.DataFrame,
    target_year: int,
    target_season: str,
    fertilizer_price: float,
) -> dict[str, Any]:
    target_season = validate_season(target_season)
    lag_1_price, lag_4_price, lag_8_price = get_lag_prices(product_history)
    fuel_price = get_fuel_for_period(target_year, target_season)
    annual_inflation = get_inflation_for_period(target_year, target_season)
    same_season_growth = (
    (lag_4_price - lag_8_price) / lag_8_price
    if lag_8_price > 0
    else 0
)
    return {
        "product_name": product_name,
        "season": target_season,
        "year": int(target_year),
        "fertilizer_price": float(fertilizer_price),
        "fuel_price": float(fuel_price),
        "annual_inflation": float(annual_inflation),
        "planted_area": latest_or_given(product_history, "planted_area", None),
        "production_amount": latest_or_given(product_history, "production_amount", None),
        "product_season": f"{product_name}_{target_season}",
        "season_year": f"{target_season}_{int(target_year)}",
        "lag_1_price": lag_1_price,
        "lag_4_price": lag_4_price,
        "lag_8_price": lag_8_price,
        "same_season_growth": same_season_growth,
    }


def predict_product_price(
    product_name: str,
    target_season: str,
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
) -> dict[str, Any]:
    df = load_dataset(dataset_path)
    product_history = get_product_history(df, product_name)

    target_year = get_target_year(target_season)
    fertilizer_price = float(get_commodity_price("urea"))

    input_row = build_prediction_input(
        product_name=product_name,
        product_history=product_history,
        target_year=target_year,
        target_season=target_season,
        fertilizer_price=fertilizer_price,
    )

    model = load_or_train_model(
        dataset_path=dataset_path,
        model_path=model_path,
    )

    prediction_df = pd.DataFrame([input_row])[FEATURE_COLUMNS]

    predicted_price = round(
        max(0.0, float(model.predict(prediction_df)[0])),
        2,
    )

    return {
        **input_row,
        "predicted_price": predicted_price,
    }


if __name__ == "__main__":
    metrics = train_price_model()

    print("\nCatBoost Model Test Metrikleri")
    print("------------------------------")
    print(f"MAE  : {metrics['mae']}")
    print(f"RMSE : {metrics['rmse']}")
    print(f"MAPE : %{metrics['mape']}")
    print(f"R2   : {metrics['r2']}")
    print(f"Satir sayisi: {int(metrics['row_count'])}")
    urunler=["DOMATES SALKIM",
             "BAKLA",
             "KARPUZ",
             "BIBER SIVRI",
             "KARNABAHAR",
             "BROKOLI"]
    season=["Winter","Spring","Summer","Fall"]
    for i in urunler:
        for j in season:
            result = predict_product_price( i,j)
            print(f"Urun          : {result['product_name']}")
            print(f"Yil           : {result['year']}")
            print(f"Sezon         : {result['season']}")
            print(f"Tahmini Fiyat : {result['predicted_price']} TL")

