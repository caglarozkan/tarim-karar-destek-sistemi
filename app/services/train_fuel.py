import os
import joblib
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


FUEL_PATH = "data/processed/data_files/seasonal_fuel_prices.csv"
MODEL_PATH = "app/models/fuel_model.pkl"

SEASON_ORDER = {
    "Winter": 1,
    "Spring": 2,
    "Summer": 3,
    "Fall": 4,
}

SEASON_SEQUENCE = ["Winter", "Spring", "Summer", "Fall"]

FEATURE_COLUMNS = ["year", "season_order", "lag_1_price", "lag_2_price", "lag_3_price", "lag_4_price"]


def load_fuel_data(path=FUEL_PATH):
    df = pd.read_csv(path)

    df = df.rename(columns={
        "Year": "year",
        "Season": "season",
        "Diesel_Price": "diesel_price"
    })

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["diesel_price"] = pd.to_numeric(df["diesel_price"], errors="coerce")
    df["season"] = df["season"].astype(str).str.strip()

    df = df.dropna(subset=["year", "season", "diesel_price"])
    df["year"] = df["year"].astype(int)

    df["season_order"] = df["season"].map(SEASON_ORDER)

    df = df.sort_values(["year", "season_order"]).reset_index(drop=True)

    df["lag_1_price"] = df["diesel_price"].shift(1)
    df["lag_2_price"] = df["diesel_price"].shift(2)
    df["lag_3_price"] = df["diesel_price"].shift(3)
    df["lag_4_price"] = df["diesel_price"].shift(4)

    df = df.dropna(subset=["lag_1_price", "lag_2_price", "lag_3_price", "lag_4_price"])
    df = df.reset_index(drop=True)

    return df


def build_pipeline(alpha=0.99):
    pipeline = Pipeline(steps=[
        ("scaler", StandardScaler()),
        ("regressor", Ridge(alpha=alpha))
    ])

    return pipeline


def evaluate_fuel_model(df, test_size=7, alpha=0.99):
    train = df.iloc[:-test_size].reset_index(drop=True)
    test = df.iloc[-test_size:].reset_index(drop=True)

    pipeline = build_pipeline(alpha=alpha)
    pipeline.fit(train[FEATURE_COLUMNS], train["diesel_price"])

    y_pred = pipeline.predict(test[FEATURE_COLUMNS])
    y_test = test["diesel_price"].values

    metrics = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "r2": round(float(r2_score(y_test, y_pred)), 4)
    }

    print("mae :", metrics["mae"])
    print("rmse:", metrics["rmse"])
    print("r2  :", metrics["r2"])

    return metrics


def train_fuel_model(path=FUEL_PATH, alpha=0.99, test_size=7):
    df = load_fuel_data(path)

    evaluate_fuel_model(df, test_size=test_size, alpha=alpha)

    pipeline = build_pipeline(alpha=alpha)
    pipeline.fit(df[FEATURE_COLUMNS], df["diesel_price"])

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    return pipeline


def load_fuel_model():
    if not os.path.exists(MODEL_PATH):
        train_fuel_model()

    return joblib.load(MODEL_PATH)


def next_season(year, season):
    idx = SEASON_SEQUENCE.index(season)

    if season == "Fall":
        return year + 1, "Winter"

    return year, SEASON_SEQUENCE[idx + 1]


def predict_fuel_series(target_year, target_season, path=FUEL_PATH):
    model = load_fuel_model()
    df = load_fuel_data(path)

    price_history = df["diesel_price"].tolist()

    last_row = df.iloc[-1]
    current_year = int(last_row["year"])
    current_season = last_row["season"]

    results = []

    while (current_year, SEASON_ORDER[current_season]) < (target_year, SEASON_ORDER[target_season]):
        next_year, next_season_name = next_season(current_year, current_season)

        row = pd.DataFrame({
            "year": [next_year],
            "season_order": [SEASON_ORDER[next_season_name]],
            "lag_1_price": [price_history[-1]],
            "lag_2_price": [price_history[-2]],
            "lag_3_price": [price_history[-3]],
            "lag_4_price": [price_history[-4]]
        })

        predicted_price = model.predict(row[FEATURE_COLUMNS])[0]

        results.append({
            "year": next_year,
            "season": next_season_name,
            "predicted_diesel_price": round(float(predicted_price), 2)
        })

        price_history.append(predicted_price)

        current_year = next_year
        current_season = next_season_name

    return pd.DataFrame(results)


def predict_fuel_price(target_year, target_season, path=FUEL_PATH):
    series = predict_fuel_series(target_year, target_season, path)

    if series.empty:
        raise ValueError("Hedef yil/sezon, mevcut veriden ileride degil.")

    son_satir = series.iloc[-1]

    return {
        "year": int(son_satir["year"]),
        "season": son_satir["season"],
        "predicted_diesel_price": float(son_satir["predicted_diesel_price"])
    }


if __name__ == "__main__":
    train_fuel_model()

