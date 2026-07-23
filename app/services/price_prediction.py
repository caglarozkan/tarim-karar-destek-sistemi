from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from app.services.fertilizer_service import get_commodity_price
from app.services.fuel_service import predict_fuel_price
from app.services.inflation_service import predict_inflation

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    mean_absolute_error,
    mean_absolute_percentage_error,
    r2_score,
    root_mean_squared_error,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

DATASET_PATH = Path("data/processed/data_files/final_price_dataset.csv")
MODEL_PATH = Path("models/price_model.pkl")

TARGET_COLUMN = "average_price"

CATEGORICAL_FEATURES = ["product_name", "season"]

NUMERIC_FEATURES = [
    "year",
    "fertilizer_price",
    "fuel_price",
    "annual_inflation",
    "planted_area",
    "production_amount",
    "lag_1_price",
    "lag_4_price",
]

FEATURE_COLUMNS = CATEGORICAL_FEATURES + NUMERIC_FEATURES

SEASON_ORDER = {
    "Winter": 1,
    "Spring": 2,
    "Summer": 3,
    "Fall": 4
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


def get_next_season(year: int, season: str) -> tuple[int, str]:
    season = validate_season(season)

    if season == "Fall":
        return year + 1, "Winter"

    current_index = SEASON_SEQUENCE.index(season)

    return year, SEASON_SEQUENCE[current_index + 1]


def get_next_n_periods_from_current(n: int = 4) -> list[tuple[int, str]]:
    current_year, current_season = get_current_season()
    periods = []

    for _ in range(n):
        current_year, current_season = get_next_season(
            current_year,
            current_season
        )
        periods.append((current_year, current_season))

    return periods


def load_dataset(dataset_path: Path = DATASET_PATH) -> pd.DataFrame:
    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Dataset bulunamadi: {dataset_path}")

    df = pd.read_csv(dataset_path)

    required_columns = [TARGET_COLUMN, *FEATURE_COLUMNS]
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Dataset eksik kolon iceriyor: {missing_columns}")

    df = df.copy()

    df["product_name"] = df["product_name"].astype(str)
    df["season"] = df["season"].astype(str).apply(validate_season)

    for column in NUMERIC_FEATURES + [TARGET_COLUMN]:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(
        subset=[TARGET_COLUMN, *FEATURE_COLUMNS]
    )

    df["year"] = df["year"].astype(int)

    return df


def build_price_model() -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    preprocessing = ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )

    model = RandomForestRegressor(
        n_estimators=400,
        random_state=42,
        min_samples_leaf=2,
    )

    return Pipeline(
        steps=[
            ("preprocessing", preprocessing),
            ("model", model),
        ]
    )


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
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    predictions = model.predict(x_test)

    sonuclar = x_test.copy()
    sonuclar["gercek"] = y_test.values
    sonuclar["tahmin"] = predictions

    sonuclar["yuzde_hata"] = (
    abs(sonuclar["gercek"] - sonuclar["tahmin"])
    / sonuclar["gercek"]
) * 100

    print(
    sonuclar.sort_values("yuzde_hata", ascending=False).head(20)
)

    metrics = {
        "mae": round(float(mean_absolute_error(y_test, predictions)), 4),
        "rmse": round(float(root_mean_squared_error(y_test, predictions)), 4),
        "mape": round(float(mean_absolute_percentage_error(y_test, predictions) * 100), 2),
        "r2": round(float(r2_score(y_test, predictions)), 4) if len(y_test) > 1 else 0.0,
        "row_count": float(len(df)),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_path)

    return metrics


def load_or_train_model(
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
) -> Pipeline:
    if not Path(model_path).exists():
        train_price_model(
            dataset_path=dataset_path,
            model_path=model_path
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


def get_lag_prices(product_history: pd.DataFrame) -> tuple[float, float]:
    lag_1_price = float(product_history.iloc[-1][TARGET_COLUMN])

    if len(product_history) >= 4:
        lag_4_price = float(product_history.iloc[-4][TARGET_COLUMN])
    else:
        lag_4_price = lag_1_price

    return lag_1_price, lag_4_price


def latest_or_given(
    product_history: pd.DataFrame,
    column: str,
    value: float | None,
) -> float:
    if value is not None:
        return float(value)

    return float(product_history.iloc[-1][column])


def get_fuel_for_period(target_year: int, target_season: str) -> float:
    return float(predict_fuel_price(target_season))


def get_inflation_for_period(target_year: int, target_season: str) -> float:
    return float(predict_inflation(target_season))


def build_prediction_input(
    product_name: str,
    product_history: pd.DataFrame,
    target_year: int,
    target_season: str,
    fertilizer_price: float,
    planted_area: float | None = None,
    production_amount: float | None = None,
    fuel_price: float | None = None,
    annual_inflation: float | None = None,
) -> dict[str, Any]:
    target_season = validate_season(target_season)

    lag_1_price, lag_4_price = get_lag_prices(product_history)

    if fuel_price is None:
        fuel_price = get_fuel_for_period(target_year, target_season)

    if annual_inflation is None:
        annual_inflation = get_inflation_for_period(target_year, target_season)

    return {
        "product_name": product_name,
        "year": int(target_year),
        "season": target_season,
        "fertilizer_price": float(fertilizer_price),
        "fuel_price": float(fuel_price),
        "annual_inflation": float(annual_inflation),
        "planted_area": latest_or_given(
            product_history,
            "planted_area",
            planted_area,
        ),
        "production_amount": latest_or_given(
            product_history,
            "production_amount",
            production_amount,
        ),
        "lag_1_price": lag_1_price,
        "lag_4_price": lag_4_price,
    }


def predict_product_price(
    product_name: str,
    target_year: int,
    target_season: str,
    planted_area: float | None = None,
    production_amount: float | None = None,
    fertilizer_price: float | None = None,
    fuel_price: float | None = None,
    annual_inflation: float | None = None,
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
) -> dict[str, Any]:
    df = load_dataset(dataset_path)
    product_history = get_product_history(df, product_name)

    if fertilizer_price is None:
        fertilizer_price = float(get_commodity_price("urea"))

    input_row = build_prediction_input(
        product_name=product_name,
        product_history=product_history,
        target_year=target_year,
        target_season=target_season,
        fertilizer_price=fertilizer_price,
        planted_area=planted_area,
        production_amount=production_amount,
        fuel_price=fuel_price,
        annual_inflation=annual_inflation,
    )

    model = load_or_train_model(
        dataset_path=dataset_path,
        model_path=model_path
    )

    prediction_df = pd.DataFrame([input_row])[FEATURE_COLUMNS]

    predicted_price = round(
        max(0.0, float(model.predict(prediction_df)[0])),
        2
    )

    return {
        **input_row,
        "predicted_price": predicted_price,
    }


def predict_products(
    product_name: str,
    planted_area: float | None = None,
    production_amount: float | None = None,
    fertilizer_price: float | None = None,
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
) -> list[dict[str, Any]]:
    df = load_dataset(dataset_path)
    product_history = get_product_history(df, product_name)

    periods = get_next_n_periods_from_current(n=4)

    if fertilizer_price is None:
        fertilizer_price = float(get_commodity_price("urea"))

    model = load_or_train_model(
        dataset_path=dataset_path,
        model_path=model_path
    )

    predictions = []

    for target_year, season in periods:
        input_row = build_prediction_input(
            product_name=product_name,
            product_history=product_history,
            target_year=target_year,
            target_season=season,
            fertilizer_price=fertilizer_price,
            planted_area=planted_area,
            production_amount=production_amount,
        )

        prediction_df = pd.DataFrame([input_row])[FEATURE_COLUMNS]

        predicted_price = round(
            max(0.0, float(model.predict(prediction_df)[0])),
            2
        )

        result = {
            **input_row,
            "predicted_price": predicted_price,
        }

        predictions.append(result)

        product_history.loc[len(product_history)] = {
            "product_name": product_name,
            "year": int(target_year),
            "season": season,
            TARGET_COLUMN: predicted_price,
            "fertilizer_price": input_row["fertilizer_price"],
            "fuel_price": input_row["fuel_price"],
            "annual_inflation": input_row["annual_inflation"],
            "planted_area": input_row["planted_area"],
            "production_amount": input_row["production_amount"],
            "lag_1_price": input_row["lag_1_price"],
            "lag_4_price": input_row["lag_4_price"],
            "_season_order": SEASON_ORDER[season],
        }

    return predictions


def predict_all_products(
    dataset_path: Path = DATASET_PATH,
    model_path: Path = MODEL_PATH,
) -> dict[str, list[dict[str, Any]]]:
    df = load_dataset(dataset_path)
    products = sorted(df["product_name"].dropna().astype(str).unique())

    return {
        product: predict_products(
            product_name=product,
            dataset_path=dataset_path,
            model_path=model_path,
        )
        for product in products
    }


def test_train_price_model():
    metrics = train_price_model()
    print("Model egitim metrikleri:")
    print(metrics)


def test_predict_products():
    product_name = "DOMATES SALKIM"

    predictions = predict_products(product_name)

    print(f"{product_name} icin sonraki 4 sezon tahmini:")

    for item in predictions:
        print(
            item["year"],
            item["season"],
            "->",
            item["predicted_price"]
        )


if __name__ == "__main__":
    train_price_model()
    test_train_price_model()
    test_predict_products()