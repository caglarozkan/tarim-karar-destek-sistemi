from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
INFLATION_PATH = KOK_DIZIN / "data" / "processed" / "data_files" / "seasonal_inflation.csv"
MODEL_PATH = KOK_DIZIN / "models" / "inflation_model.pkl"

TARGET_COLUMN = "annual_inflation"

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


def validate_season(season: str) -> str:
    if season not in SEASON_ORDER:
        valid_seasons = ", ".join(SEASONS)
        raise ValueError(f"Gecersiz sezon: {season}. Gecerli sezonlar: {valid_seasons}")
    return season


def load_raw_inflation_data(path: Path = INFLATION_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(f"Enflasyon veri dosyasi bulunamadi: {path}")

    df = pd.read_csv(path)

    required_columns = ["year", "season", TARGET_COLUMN]
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Enflasyon datasinda eksik kolon var: {missing_columns}")

    df = df.copy()
    df["year"] = df["year"].astype(int)
    df["season"] = df["season"].astype(str)
    df["season"] = df["season"].apply(validate_season)
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(float)
    df["season_order"] = df["season"].map(SEASON_ORDER)

    return df.sort_values(["year", "season_order"]).reset_index(drop=True)


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["lag_1"] = df[TARGET_COLUMN].shift(1)
    df["lag_2"] = df[TARGET_COLUMN].shift(2)
    df["lag_3"] = df[TARGET_COLUMN].shift(3)
    df["lag_4"] = df[TARGET_COLUMN].shift(4)
    df["rolling_mean_3"] = df[TARGET_COLUMN].shift(1).rolling(3).mean()
    df["rolling_std_3"] = df[TARGET_COLUMN].shift(1).rolling(3).std()

    return df.dropna().reset_index(drop=True)


def load_inflation_data(path: Path = INFLATION_PATH) -> pd.DataFrame:
    raw_df = load_raw_inflation_data(path)
    return add_time_features(raw_df)


def build_pipeline(alpha: float = 1.0) -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            ("season", OneHotEncoder(handle_unknown="ignore"), ["season"]),
            ("num", StandardScaler(),
                [  "year",
                    "lag_1",
                    "lag_2",
                    "lag_3",
                    "lag_4",
                    "rolling_mean_3",
                    "rolling_std_3",
                ],
            ),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("regressor", Ridge(alpha=alpha)),
        ]
    )


def evaluate_inflation_model(
    df: pd.DataFrame,
    test_size: int = 8,
    alpha: float = 1.0,
) -> dict[str, float]:
    if len(df) <= test_size:
        raise ValueError("Test icin yeterli enflasyon verisi yok.")

    train = df.iloc[:-test_size].reset_index(drop=True)
    test = df.iloc[-test_size:].reset_index(drop=True)

    pipeline = build_pipeline(alpha=alpha)
    pipeline.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])

    y_pred = pipeline.predict(test[FEATURE_COLUMNS])
    y_test = test[TARGET_COLUMN].values

    non_zero_mask = y_test != 0
    if non_zero_mask.any():
        mape = np.mean(np.abs((y_test[non_zero_mask] - y_pred[non_zero_mask]) / y_test[non_zero_mask])) * 100
    else:
        mape = 0.0

    metrics = {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "r2": round(float(r2_score(y_test, y_pred)), 4),
        "mape": round(float(mape), 2),
    }

    return metrics


def train_inflation_model(
    path: Path = INFLATION_PATH,
    model_path: Path = MODEL_PATH,
    alpha: float = 1.0,
    test_size: int = 8,
) -> tuple[Pipeline, dict[str, float]]:
    df = load_inflation_data(path)
    metrics = evaluate_inflation_model(df, test_size=test_size, alpha=alpha)

    pipeline = build_pipeline(alpha=alpha)
    pipeline.fit(df[FEATURE_COLUMNS], df[TARGET_COLUMN])

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)

    return pipeline, metrics


def load_inflation_model(
    path: Path = INFLATION_PATH,
    model_path: Path = MODEL_PATH,
) -> Pipeline:
    if not model_path.exists():
        train_inflation_model(path=path, model_path=model_path)

    return joblib.load(model_path)


def get_next_period(year: int, season: str) -> tuple[int, str]:
    validate_season(season)

    season_index = SEASONS.index(season) + 1
    if season_index == len(SEASONS):
        return year + 1, SEASONS[0]

    return year, SEASONS[season_index]


def get_upcoming_periods_until_target(
    last_year: int,
    last_season: str,
    target_season: str,
) -> list[tuple[int, str]]:
    target_season = validate_season(target_season)
    current_year = int(last_year)
    current_season = validate_season(last_season)
    periods = []

    while True:
        current_year, current_season = get_next_period(current_year, current_season)
        periods.append((current_year, current_season))

        if current_season == target_season:
            break

    return periods


def make_prediction_row(history: pd.DataFrame, year: int, season: str) -> pd.DataFrame:
    last_values = history[TARGET_COLUMN]

    if len(last_values) < 4:
        raise ValueError("Tahmin icin en az 4 sezonluk enflasyon verisi gerekir.")

    lag_1 = float(last_values.iloc[-1])
    lag_2 = float(last_values.iloc[-2])
    lag_3 = float(last_values.iloc[-3])
    lag_4 = float(last_values.iloc[-4])

    return pd.DataFrame(
        {
            "year": [int(year)],
            "season": [season],
            "lag_1": [lag_1],
            "lag_2": [lag_2],
            "lag_3": [lag_3],
            "lag_4": [lag_4],
            "rolling_mean_3": [float(np.mean([lag_1, lag_2, lag_3]))],
            "rolling_std_3": [float(np.std([lag_1, lag_2, lag_3], ddof=1))],
        }
    )


def predict_inflation_series(
    target_year_or_season: int | str,
    target_season: str | None = None,
    path: Path = INFLATION_PATH,
    model_path: Path = MODEL_PATH,
) -> pd.DataFrame:
    model = load_inflation_model(path=path, model_path=model_path)
    history = load_raw_inflation_data(path)

    current_year = int(history.iloc[-1]["year"])
    current_season = str(history.iloc[-1]["season"])

    if target_season is None:
        target_year = None
        target_season = validate_season(str(target_year_or_season))
    else:
        target_year = int(target_year_or_season)
        target_season = validate_season(target_season)

    if target_year is None:
        periods = get_upcoming_periods_until_target(
            last_year=current_year,
            last_season=current_season,
            target_season=target_season,
        )
    else:
        periods = []
        while (current_year, SEASON_ORDER[current_season]) < (
            int(target_year),
            SEASON_ORDER[target_season],
        ):
            current_year, current_season = get_next_period(current_year, current_season)
            periods.append((current_year, current_season))

    predictions = []

    for prediction_year, prediction_season in periods:
        sample = make_prediction_row(history, prediction_year, prediction_season)
        predicted_inflation = float(model.predict(sample[FEATURE_COLUMNS])[0])

        predictions.append({
            "year": int(prediction_year),
            "season": prediction_season,
            "annual_inflation": round(predicted_inflation, 2),
        })

        history.loc[len(history)] = {
            "year": int(prediction_year),
            "season": prediction_season,
            "annual_inflation": predicted_inflation,
            "season_order": SEASON_ORDER[prediction_season],
        }

    return pd.DataFrame(predictions)


def predict_inflation(
    target_year_or_season: int | str,
    target_season: str | None = None,
    path: Path = INFLATION_PATH,
    model_path: Path = MODEL_PATH,
) -> float:
    series = predict_inflation_series(
        target_year_or_season=target_year_or_season,
        target_season=target_season,
        path=path,
        model_path=model_path,
    )

    if series.empty:
        raise ValueError("Hedef yil/sezon, mevcut veriden ileride degil.")

    last_row = series.iloc[-1]
    return float(last_row["annual_inflation"])


if __name__ == "__main__":
    model, model_metrics = train_inflation_model()



