import pandas as pd
import numpy as np

df = pd.read_csv(
    "data/raw_data/fertilizer/gübre.csv",
    sep=";",
    encoding="ISO-8859-1"
)

df.columns = [
    "YIL",
    "Amonyum_Sulfat",
    "CAN",
    "Ure",
    "DAP",
    "Gubre_20_20_0"
]

df = df.drop(index=[0, 1]).reset_index(drop=True)


def clean_price(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip()
    value = value.replace(".", "")
    value = value.replace(",", ".")

    return pd.to_numeric(value, errors="coerce")


price_columns = [
    "Amonyum_Sulfat",
    "CAN",
    "Ure",
    "DAP",
    "Gubre_20_20_0"
]

for col in price_columns:
    df[col] = df[col].apply(clean_price)

df["YIL"] = df["YIL"].replace({
    "2021 (1. Yar?)": "2021",
    "2021 (2. Yar?)": "2021",
    "2022-1": "2022"
})

df = df.rename(columns={"YIL": "Year"})

df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
df = df.dropna(subset=["Year"])
df["Year"] = df["Year"].astype(int)

df["Ortalama_Gubre_Maliyeti_Ton_TL"] = (
    df[["Amonyum_Sulfat", "CAN", "Ure"]].mean(axis=1)
).round(2)

df = (
    df.groupby("Year", as_index=False)
    .mean(numeric_only=True)
)

df["Ortalama_Gubre_Maliyeti_Ton_TL"] = df["Ortalama_Gubre_Maliyeti_Ton_TL"].round(2)

print(df.tail(10))
df =df.rename(columns={
    "ProductName": "product_name",
    "Year": "year",
    "District": "district",
    "Ekilen Alan": "planted_area",
    "Üretim Miktarı": "production_amount",
    "FUEL_PRICE": "fuel_price",
    "Ortalama_Gubre_Maliyeti_Ton_TL": "fertilizer_price",
    "URUN_ADI": "product_name",
    "ORTALAMA_FIYAT": "average_price",
    "YIL": "year",
    "SEZON": "season"
})
df.to_csv(
    "data/processed/data_files/cleaned_fertilizer.csv",
    index=False,
    encoding="utf-8-sig"
)