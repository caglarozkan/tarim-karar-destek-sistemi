from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent.parent.parent

INPUT_PATH = ROOT / "data" / "processed" / "data_files" / "final_optimization.csv"
OUTPUT_PATH = ROOT / "data" / "processed" / "data_files" / "predict_yield_per_decare.csv"


TARGET_YEAR = 2026

GROUP_COLUMNS = [
    "product_name",
    "province",
    "district",
    "season",
]


def predict_next_yield(group):
    yearly = (
        group.groupby("year", as_index=False)
        .agg(yield_per_decare_kg=("yield_per_decare_kg", "mean"))
        .dropna()
        .sort_values("year")
    )

    if yearly.empty:
        return None

    if len(yearly) == 1:
        return float(yearly["yield_per_decare_kg"].iloc[0])

    x = yearly["year"].to_numpy(dtype=float)
    y = yearly["yield_per_decare_kg"].to_numpy(dtype=float)

    slope, intercept = np.polyfit(x, y, 1)
    prediction = slope * TARGET_YEAR + intercept

    if prediction <= 0:
        prediction = y.mean()

    return round(float(prediction), 2)


def main():
    df = pd.read_csv(INPUT_PATH)

    required_columns = [
        "product_name",
        "year",
        "planted_area",
        "production_amount",
        "season",
        "province",
        "district",
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Eksik kolonlar: {missing_columns}")

    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["planted_area"] = pd.to_numeric(df["planted_area"], errors="coerce")
    df["production_amount"] = pd.to_numeric(df["production_amount"], errors="coerce")

    if "yield_per_decare_kg" not in df.columns:
        df["yield_per_decare_kg"] = (
            df["production_amount"] * 1000 / df["planted_area"]
        )
    else:
        df["yield_per_decare_kg"] = pd.to_numeric(
            df["yield_per_decare_kg"],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "product_name",
            "year",
            "planted_area",
            "production_amount",
            "yield_per_decare_kg",
            "province",
            "district",
            "season",
        ]
    )

    df = df[
        (df["planted_area"] > 0)
        & (df["production_amount"] > 0)
        & (df["yield_per_decare_kg"] > 0)
    ]

    results = []

    for group_values, group in df.groupby(GROUP_COLUMNS):
        predicted_yield = predict_next_yield(group)

        if predicted_yield is None:
            continue

        row = dict(zip(GROUP_COLUMNS, group_values))
        row["year"] = TARGET_YEAR
        row["predicted_yield_per_decare_kg"] = predicted_yield

        results.append(row)

    result_df = pd.DataFrame(results)

    result_df = result_df.sort_values(
        ["province", "district", "product_name", "season"]
    ).reset_index(drop=True)

    result_df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")

    print(f"2026 yield tahminleri kaydedildi: {OUTPUT_PATH}")
    print(result_df.head(20))


if __name__ == "__main__":
    main()