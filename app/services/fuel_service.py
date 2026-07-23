from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


FUEL_PATH = Path("data/processed/data_files/seasonal_fuel_prices.csv")
MODEL_PATH = Path("models/fuel_model.pkl")

TARGET_COLUMN = "diesel_price"

SEASON_ORDER = {
    "Winter": 1,
    "Spring": 2,
    "Summer": 3,
    "Fall": 4,
}

SEASON_SEQUENCE = ["Winter", "Spring", "Summer", "Fall"]

FEATURE_COLUMNS = [
    "year",
    "season_order",
    "lag_1_price",
    "lag_2_price",
    "lag_3_price",
    "lag_4_price",
]


def validate_season(season: str) -> str:
    if season not in SEASON_ORDER:
        valid_seasons = ", ".join(SEASON_SEQUENCE)
        raise ValueError(f"Gecersiz sezon: {season}. Gecerli sezonlar: {valid_seasons}")
    return season


def load_raw_fuel_data(path: Path = FUEL_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        raise FileNotFoundError(f"Yakit veri dosyasi bulunamadi: {path}")

    df = pd.read_csv(path)

    df = df.rename(
        columns={
            "Year": "year",
            "Season": "season",
            "Diesel_Price": TARGET_COLUMN,
        }
    )

    required_columns = ["year", "season", TARGET_COLUMN]
    missing_columns = [
        column for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(f"Yakit datasinda eksik kolon var: {missing_columns}")

    df = df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors="coerce")
    df["season"] = df["season"].astype(str).str.strip()

    df = df.dropna(subset=["year", "season", TARGET_COLUMN])
    df["year"] = df["year"].astype(int)
    df["season"] = df["season"].apply(validate_season)
    df["season_order"] = df["season"].map(SEASON_ORDER)

    return df.sort_values(["year", "season_order"]).reset_index(drop=True)


def add_lag_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["lag_1_price"] = df[TARGET_COLUMN].shift(1)
    df["lag_2_price"] = df[TARGET_COLUMN].shift(2)
    df["lag_3_price"] = df[TARGET_COLUMN].shift(3)
    df["lag_4_price"] = df[TARGET_COLUMN].shift(4)

    return df.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)


def load_fuel_data(path: Path = FUEL_PATH) -> pd.DataFrame:
    raw_df = load_raw_fuel_data(path)
    return add_lag_features(raw_df)


def build_pipeline(alpha: float = 0.99) -> Pipeline:
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("regressor", Ridge(alpha=alpha)),
        ]
    )


def evaluate_fuel_model(
    df: pd.DataFrame,
    test_size: int = 7,
    alpha: float = 0.99,
) -> dict[str, float]:
    if len(df) <= test_size:
        raise ValueError("Test icin yeterli yakit verisi yok.")

    train = df.iloc[:-test_size].reset_index(drop=True)
    test = df.iloc[-test_size:].reset_index(drop=True)

    pipeline = build_pipeline(alpha=alpha)
    pipeline.fit(train[FEATURE_COLUMNS], train[TARGET_COLUMN])

    y_pred = pipeline.predict(test[FEATURE_COLUMNS])
    y_test = test[TARGET_COLUMN].values

    return {
        "mae": round(float(mean_absolute_error(y_test, y_pred)), 4),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, y_pred))), 4),
        "r2": round(float(r2_score(y_test, y_pred)), 4),
    }


def train_fuel_model(
    path: Path = FUEL_PATH,
    model_path: Path = MODEL_PATH,
    alpha: float = 0.99,
    test_size: int = 7,
) -> tuple[Pipeline, dict[str, float]]:
    df = load_fuel_data(path)
    metrics = evaluate_fuel_model(df, test_size=test_size, alpha=alpha)

    pipeline = build_pipeline(alpha=alpha)
    pipeline.fit(df[FEATURE_COLUMNS], df[TARGET_COLUMN])

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)

    return pipeline, metrics


def load_fuel_model(
    path: Path = FUEL_PATH,
    model_path: Path = MODEL_PATH,
) -> Pipeline:
    if not model_path.exists():
        train_fuel_model(path=path, model_path=model_path)

    return joblib.load(model_path)


def get_next_season(year: int, season: str) -> tuple[int, str]:
    validate_season(season)

    if season == "Fall":
        return year + 1, "Winter"

    current_index = SEASON_SEQUENCE.index(season)
    return year, SEASON_SEQUENCE[current_index + 1]


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
        current_year, current_season = get_next_season(current_year, current_season)
        periods.append((current_year, current_season))

        if current_season == target_season:
            break

    return periods


def make_prediction_row(
    price_history: list[float],
    year: int,
    season: str,
) -> pd.DataFrame:
    if len(price_history) < 4:
        raise ValueError("Tahmin icin en az 4 sezonluk yakit fiyati gerekir.")

    return pd.DataFrame(
        {
            "year": [int(year)],
            "season_order": [SEASON_ORDER[season]],
            "lag_1_price": [float(price_history[-1])],
            "lag_2_price": [float(price_history[-2])],
            "lag_3_price": [float(price_history[-3])],
            "lag_4_price": [float(price_history[-4])],
        }
    )


def predict_fuel_series(
    target_year_or_season: int | str,
    target_season: str | None = None,
    path: Path = FUEL_PATH,
    model_path: Path = MODEL_PATH,
) -> pd.DataFrame:
    model = load_fuel_model(path=path, model_path=model_path)
    history = load_raw_fuel_data(path)

    price_history = history[TARGET_COLUMN].astype(float).tolist()

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
            current_year, current_season = get_next_season(current_year, current_season)
            periods.append((current_year, current_season))

    results = []

    for prediction_year, prediction_season in periods:
        row = make_prediction_row(
            price_history=price_history,
            year=prediction_year,
            season=prediction_season,
        )

        predicted_price = float(model.predict(row[FEATURE_COLUMNS])[0])

        results.append(
            {
                "year": int(prediction_year),
                "season": prediction_season,
                "predicted_diesel_price": round(predicted_price, 2),
            }
        )

        price_history.append(predicted_price)

    return pd.DataFrame(results)


def predict_fuel_price(
    target_year_or_season: int | str,
    target_season: str | None = None,
    path: Path = FUEL_PATH,
    model_path: Path = MODEL_PATH,
) -> float:
    series = predict_fuel_series(
        target_year_or_season=target_year_or_season,
        target_season=target_season,
        path=path,
        model_path=model_path,
    )

    if series.empty:
        raise ValueError("Hedef yil/sezon, mevcut veriden ileride degil.")

    last_row = series.iloc[-1]
    return float(last_row["predicted_diesel_price"])


def predict_upcoming_fuel_series(
    target_season: str,
    path: Path = FUEL_PATH,
    model_path: Path = MODEL_PATH,
) -> pd.DataFrame:
    return predict_fuel_series(
        target_year_or_season=target_season,
        path=path,
        model_path=model_path,
    )


def predict_upcoming_fuel_price(
    target_season: str,
    path: Path = FUEL_PATH,
    model_path: Path = MODEL_PATH,
) -> float:
    return predict_fuel_price(
        target_year_or_season=target_season,
        path=path,
        model_path=model_path,
    )


if __name__ == "__main__":
    model, model_metrics = train_fuel_model()

