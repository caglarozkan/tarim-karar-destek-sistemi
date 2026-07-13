import pandas as pd
import numpy as np

market = pd.read_csv("data/processed/data_files/cleaned_all_marketplace.csv")

market["TARIH"] = pd.to_datetime(
    market["TARIH"],
    format="%Y-%m-%d",
    errors="coerce"
)

market["YIL"] = market["TARIH"].dt.year
market["AY"] = market["TARIH"].dt.month

def get_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Fall"

market["SEZON"] = market["AY"].apply(get_season)

price_table = (
    market
    .groupby(
        ["URUN_ADI", "YIL", "SEZON"],
        as_index=False
    )
    .agg(
        AveragePrice=("ORTALAMA_FIYAT", "mean")
    )
)

market=market.iloc[:,3:]
market=market.drop(columns=["AY","ASGARI_FIYAT","AZAMI_FIYAT","BIRIM"])
market=market[market["URUN_ADI"].isin(["DOMATES  SALKIM","SALATALIK  SİLOR","KABAK  SAKIZ","KARPUZ","SOGAN  KURU"])]
market=market.reset_index(drop=True)
market =market.rename(columns={
    "URUN_ADI": "product_name",
    "ORTALAMA_FIYAT": "average_price",
    "YIL": "year",
    "SEZON": "season"
})
market.to_csv("data/processed/data_files/final_price_dataset.csv")