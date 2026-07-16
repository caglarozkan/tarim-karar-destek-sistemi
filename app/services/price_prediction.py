import os
import joblib
import pandas as pd
import numpy as np

from xgboost import XGBRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


DATA_PATH = "data/processed/data_files/final_price_dataset.csv"
MODEL_PATH = "app/models/price_model.pkl"

SEASONS = ["Winter", "Spring", "Summer", "Fall"]


def normalize_product_name(product_name):
    return str(product_name).strip().upper()


def normalize_season(season):
    season = str(season).strip().capitalize()

    season_map = {
        "Winter": "Winter",
        "Spring": "Spring",
        "Summer": "Summer",
        "Fall": "Fall",
        "Autumn": "Fall",
        "Kis": "Winter",
        "Kış": "Winter",
        "Ilkbahar": "Spring",
        "İlkbahar": "Spring",
        "Yaz": "Summer",
        "Sonbahar": "Fall",
    }

    if season not in season_map:
        raise ValueError("Geçersiz sezon. Winter, Spring, Summer veya Fall gönderilmeli.")

    return season_map[season]


def load_price_data():
    df = pd.read_csv(DATA_PATH)

    df = df[
        [
            "product_name",
            "average_price",
            "year",
            "season",
            "fertilizer_price",
            "fuel_price",
            "annual_inflation",
            "lag_1_price",
            "lag_4_price",
        ]
    ].copy()

    df["product_name"] = df["product_name"].apply(normalize_product_name)
    df["season"] = df["season"].astype(str).str.strip()

    numeric_columns = [
        "average_price",
        "year",
        "fertilizer_price",
        "fuel_price",
        "annual_inflation",
        "lag_1_price",
        "lag_4_price",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=[
            "product_name",
            "average_price",
            "year",
            "season",
            "fertilizer_price",
            "fuel_price",
            "annual_inflation",
            "lag_1_price",
            "lag_4_price",
        ]
    )

    df["year"] = df["year"].astype(int)

    return df


def train_price_model():
    df = load_price_data()

    X = df[
        [
            "product_name",
            "year",
            "season",
            "fertilizer_price",
            "fuel_price",
            "annual_inflation",
            "lag_1_price",
            "lag_4_price",
        ]
    ]

    y = df["average_price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore"),
                ["product_name", "season"]
            ),
            (
                "num",
                "passthrough",
                [
                    "year",
                    "fertilizer_price",
                    "fuel_price",
                    "annual_inflation",
                    "lag_1_price",
                    "lag_4_price",
                ]
            )
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "regressor",
                XGBRegressor(
                    n_estimators=500,
                    learning_rate=0.05,
                    max_depth=6,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    objective="reg:squarederror",
                    random_state=42,
                    n_jobs=-1,
                )
            )
        ]
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    metrics = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "r2": round(float(r2_score(y_test, y_pred)), 4),
    }

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return metrics


def load_price_model():
    if not os.path.exists(MODEL_PATH):
        train_price_model()

    return joblib.load(MODEL_PATH)


def get_prediction_features(product_name, season, year=None):
    df = load_price_data()

    product_name = normalize_product_name(product_name)
    season = normalize_season(season)

    product_df = df[df["product_name"] == product_name].copy()

    if product_df.empty:
        raise ValueError(f"Ürün bulunamadı: {product_name}")

    product_df = product_df.sort_values(["year", "season"])

    latest_row = product_df.sort_values("year").iloc[-1]

    if year is None:
        year = int(latest_row["year"])

    same_season_rows = product_df[
        (product_df["season"] == season) &
        (product_df["year"] <= year)
    ].sort_values("year")

    if not same_season_rows.empty:
        base_row = same_season_rows.iloc[-1]
    else:
        base_row = latest_row

    input_df = pd.DataFrame({
        "product_name": [product_name],
        "year": [year],
        "season": [season],
        "fertilizer_price": [base_row["fertilizer_price"]],
        "fuel_price": [base_row["fuel_price"]],
        "annual_inflation": [base_row["annual_inflation"]],
        "lag_1_price": [base_row["lag_1_price"]],
        "lag_4_price": [base_row["lag_4_price"]],
    })

    return input_df


def predict_price_from_user(product_name, season, year=None):
    model = load_price_model()

    input_df = get_prediction_features(
        product_name=product_name,
        season=season,
        year=year
    )

    prediction = model.predict(input_df)[0]

    return {
        "product_name": input_df.loc[0, "product_name"],
        "season": input_df.loc[0, "season"],
        "year": int(input_df.loc[0, "year"]),
        "predicted_price": round(float(prediction), 2)
    }


if __name__ == "__main__":
    result = predict_price_from_user(
        product_name="BIBER SIVRI",
        season="Fall",
    )

    print(result)