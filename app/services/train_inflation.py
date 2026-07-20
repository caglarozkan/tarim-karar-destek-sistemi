import os
import joblib
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Ridge, RidgeCV
from sklearn.model_selection import TimeSeriesSplit
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


INFLATION_PATH = "data/processed/data_files/seasonal_inflation.csv"
MODEL_PATH = "app/models/inflation_model.pkl"

SEASON_ORDER = {
    "Winter": 0,
    "Spring": 1,
    "Summer": 2,
    "Fall": 3,
}

SEASONS = ["Winter", "Spring", "Summer", "Fall"]

FEATURE_COLUMNS = [
    "year",
    "season",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_4",
    "rolling_mean_3",
    "rolling_std_3",
]


def load_inflation_data(path=INFLATION_PATH):
    df = pd.read_csv(path)

    df["year"] = df["year"].astype(int)

    df["season_order"] = df["season"].map(SEASON_ORDER)

    df = df.sort_values(["year", "season_order"]).reset_index(drop=True)

    df["lag_1"] = df["annual_inflation"].shift(1)
    df["lag_2"] = df["annual_inflation"].shift(2)
    df["lag_3"] = df["annual_inflation"].shift(3)
    df["lag_4"] = df["annual_inflation"].shift(4)

    df["rolling_mean_3"] = df["annual_inflation"].shift(1).rolling(3).mean()
    df["rolling_std_3"] = df["annual_inflation"].shift(1).rolling(3).std()

    df = df.dropna().reset_index(drop=True)

    return df


def build_pipeline(alpha=1.0):
    preprocessor = ColumnTransformer(
        transformers=[
            ("season", OneHotEncoder(handle_unknown="ignore"), ["season"]),
            ("num", StandardScaler(), [
                "year", "lag_1", "lag_2", "lag_3", "lag_4",
                "rolling_mean_3", "rolling_std_3"
            ]),
        ]
    )

    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor", Ridge(alpha=alpha)),
    ])

    return pipeline


def find_best_alpha(df, alphas=(0.01, 0.1, 0.5, 1.0, 5.0, 10.0, 50.0)):
    tscv = TimeSeriesSplit(n_splits=5)
    en_iyi_alpha = None
    en_iyi_mae = float("inf")

    for alpha in alphas:
        hatalar = []
        for train_idx, test_idx in tscv.split(df):
            train = df.iloc[train_idx]
            test = df.iloc[test_idx]

            pipeline = build_pipeline(alpha=alpha)
            pipeline.fit(train[FEATURE_COLUMNS], train["annual_inflation"])

            pred = pipeline.predict(test[FEATURE_COLUMNS])
            hatalar.append(mean_absolute_error(test["annual_inflation"], pred))

        ortalama_mae = np.mean(hatalar)
        print(f"alpha={alpha:<6} ortalama MAE={ortalama_mae:.4f}")

        if ortalama_mae < en_iyi_mae:
            en_iyi_mae = ortalama_mae
            en_iyi_alpha = alpha

    print(f"\nEn iyi alpha: {en_iyi_alpha}")
    return en_iyi_alpha


def walk_forward_backtest(df, n_test=8, alpha=1.0):
    results = []

    for i in range(len(df) - n_test, len(df)):
        train = df.iloc[:i]
        test_row = df.iloc[[i]]

        pipeline = build_pipeline(alpha=alpha)
        pipeline.fit(train[FEATURE_COLUMNS], train["annual_inflation"])

        pred = pipeline.predict(test_row[FEATURE_COLUMNS])[0]
        gercek = test_row["annual_inflation"].values[0]

        results.append({
            "year": test_row["year"].values[0],
            "season": test_row["season"].values[0],
            "gercek": gercek,
            "tahmin": pred
        })

    sonuc_df = pd.DataFrame(results)

    mae = mean_absolute_error(sonuc_df["gercek"], sonuc_df["tahmin"])
    rmse = np.sqrt(mean_squared_error(sonuc_df["gercek"], sonuc_df["tahmin"]))
    r2 = r2_score(sonuc_df["gercek"], sonuc_df["tahmin"])

    print("=== Walk-Forward Backtest ===")
    print("MAE :", round(mae, 4))
    print("RMSE:", round(rmse, 4))
    print("R2  :", round(r2, 4))

    return sonuc_df


def compare_with_random_forest(df, test_size=8):
    train = df.iloc[:-test_size].reset_index(drop=True)
    test = df.iloc[-test_size:].reset_index(drop=True)

    X_train = pd.get_dummies(train[FEATURE_COLUMNS], columns=["season"])
    X_test = pd.get_dummies(test[FEATURE_COLUMNS], columns=["season"])
    X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

    rf = RandomForestRegressor(n_estimators=300, max_depth=5, random_state=42)
    rf.fit(X_train, train["annual_inflation"])

    pred = rf.predict(X_test)
    y_test = test["annual_inflation"].values

    print("=== Random Forest Karsilastirma ===")
    print("MAE :", round(mean_absolute_error(y_test, pred), 4))
    print("RMSE:", round(np.sqrt(mean_squared_error(y_test, pred)), 4))
    print("R2  :", round(r2_score(y_test, pred), 4))


def evaluate_inflation_model(df, test_size=8, alpha=1.0):
    train = df.iloc[:-test_size].reset_index(drop=True)
    test = df.iloc[-test_size:].reset_index(drop=True)

    pipeline = build_pipeline(alpha=alpha)
    pipeline.fit(train[FEATURE_COLUMNS], train["annual_inflation"])

    y_pred = pipeline.predict(test[FEATURE_COLUMNS])
    y_test = test["annual_inflation"].values

    metrics = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "r2": round(float(r2_score(y_test, y_pred)), 4),
        "mape": round(float(np.mean(np.abs((y_test - y_pred) / y_test)) * 100), 2),
    }

    print("mae :", metrics["mae"])
    print("rmse:", metrics["rmse"])
    print("r2  :", metrics["r2"])
    print("mape: %", metrics["mape"])

    return metrics


def train_inflation_model(path=INFLATION_PATH, alpha=1.0, test_size=8):
    df = load_inflation_data(path)

    evaluate_inflation_model(df, test_size=test_size, alpha=alpha)

    pipeline = build_pipeline(alpha=alpha)
    pipeline.fit(df[FEATURE_COLUMNS], df["annual_inflation"])

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)

    return pipeline


def load_inflation_model():
    if not os.path.exists(MODEL_PATH):
        train_inflation_model()

    return joblib.load(MODEL_PATH)


def predict_inflation_series(target_year, target_season, path=INFLATION_PATH):
    model = load_inflation_model()
    history = load_inflation_data(path)

    predictions = []

    year = history.iloc[-1]["year"]
    season_index = SEASONS.index(history.iloc[-1]["season"])

    while (year, season_index) < (target_year, SEASONS.index(target_season)):
        season_index += 1

        if season_index == 4:
            season_index = 0
            year += 1

        season = SEASONS[season_index]

        last = history["annual_inflation"]
        lag1 = last.iloc[-1]
        lag2 = last.iloc[-2]
        lag3 = last.iloc[-3]
        lag4 = last.iloc[-4]

        rolling_mean = np.mean([lag1, lag2, lag3])
        rolling_std = np.std([lag1, lag2, lag3])

        sample = pd.DataFrame({
            "year": [year],
            "season": [season],
            "lag_1": [lag1],
            "lag_2": [lag2],
            "lag_3": [lag3],
            "lag_4": [lag4],
            "rolling_mean_3": [rolling_mean],
            "rolling_std_3": [rolling_std],
        })

        pred = model.predict(sample[FEATURE_COLUMNS])[0]

        predictions.append({
            "year": int(year),
            "season": season,
            "annual_inflation": round(float(pred), 2),
        })

        history.loc[len(history)] = {
            "year": year,
            "season": season,
            "annual_inflation": pred,
        }

    return pd.DataFrame(predictions)


def predict_inflation(target_year, target_season, path=INFLATION_PATH):
    series = predict_inflation_series(target_year, target_season, path)

    if series.empty:
        raise ValueError("Hedef yil/sezon, mevcut veriden ileride degil.")

    son_satir = series.iloc[-1]

    return {
        "year": int(son_satir["year"]),
        "season": son_satir["season"],
        "predicted_annual_inflation": float(son_satir["annual_inflation"]),
    }


if __name__ == "__main__":
    df = load_inflation_data(INFLATION_PATH)

    walk_forward_backtest(df, n_test=8, alpha=1.0)