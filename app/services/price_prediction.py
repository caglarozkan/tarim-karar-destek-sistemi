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


def load_price_data():
    df = pd.read_csv(DATA_PATH)

    df = df[["product_name", "average_price", "year", "season"]].copy()
    df = df.dropna(subset=["product_name", "average_price", "year", "season"])

    df["product_name"] = df["product_name"].astype(str).str.strip().str.upper()
    df["season"] = df["season"].astype(str).str.strip()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["average_price"] = pd.to_numeric(df["average_price"], errors="coerce")

    df = df.dropna(subset=["year", "average_price"])
    df["year"] = df["year"].astype(int)

    return df

def train_price_model():
    df = load_price_data()

    X = df[["product_name", "year", "season"]]
    y = df["average_price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), ["product_name", "season"]),
            ("num", "passthrough", ["year"])
        ]
    )

    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", XGBRegressor(
                n_estimators=500,
                learning_rate=0.05,
                max_depth=6,
                subsample=0.8,
                colsample_bytree=0.8,
                objective="reg:squarederror",
                random_state=42,
                n_jobs=-1
            ))
        ]
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    metrics = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "r2": round(float(r2_score(y_test, y_pred)), 4)
    }

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    return metrics


def load_price_model():
    if not os.path.exists(MODEL_PATH):
        train_price_model()

    return joblib.load(MODEL_PATH)


def predict_price(product_name, year, season):
    model = load_price_model()

    input_df = pd.DataFrame({
        "product_name": [product_name],
        "year": [year],
        "season": [season]
    })

    input_df["product_name"] = input_df["product_name"].astype(str).str.strip().str.upper()
    input_df["season"] = input_df["season"].astype(str).str.strip()
    input_df["year"] = pd.to_numeric(input_df["year"], errors="coerce").astype(int)

    prediction = model.predict(input_df)[0]

    return {
        "product_name": input_df.loc[0, "product_name"],
        "year": int(input_df.loc[0, "year"]),
        "season": input_df.loc[0, "season"],
        "predicted_price": round(float(prediction), 2)
    }


def predict_next_seasons(product_name, start_year=2026, start_season="Fall", count=4):
    seasons = ["Winter", "Spring", "Summer", "Fall"]

    current_year = int(start_year)
    current_season = start_season

    results = []

    for _ in range(count):
        prediction = predict_price(
            product_name=product_name,
            year=current_year,
            season=current_season
        )

        results.append(prediction)

        season_index = seasons.index(current_season)

        if current_season == "Fall":
            current_year += 1
            current_season = "Winter"
        else:
            current_season = seasons[season_index + 1]

    return results