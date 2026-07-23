import numpy as np 
import pandas as pd

def dosya_oku(dosya):
    df=pd.read_excel(dosya)
    return df

def dosya_temizle(df):
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df = df.reset_index(drop=True)
    df = df[[
    "Şehir",
    "İlçe",
    "Tarih",
    "V/Pro Diesel",
    "V/Max Diesel"
]]

    df["V/Pro Diesel"] = (
        df["V/Pro Diesel"].astype(str)
        .str.replace("TL/LT", "", regex=False)
        .str.strip()
    )
    df["V/Max Diesel"] = (
        df["V/Max Diesel"].astype(str)
        .str.replace("TL/LT", "", regex=False)
        .str.strip()
    )
    df=df.rename(columns={
    "Şehir":"province",
    "İlçe":"district",
    "Tarih":"date"
    })
    return df

dosyalar=[
    "data/raw_data/fuel/2014_fuel_fall.xlsx",
    "data/raw_data/fuel/2015_fuel_fall.xlsx",
    "data/raw_data/fuel/2016_fuel_fall.xlsx",
    "data/raw_data/fuel/2017_fuel_fall.xlsx",
    "data/raw_data/fuel/2018_fuel_fall.xlsx",
    "data/raw_data/fuel/2019_fuel_fall.xlsx",
    "data/raw_data/fuel/2020_fuel_fall.xlsx",
    "data/raw_data/fuel/2021_fuel_fall.xlsx",
    "data/raw_data/fuel/2022_fuel_fall.xlsx",
    "data/raw_data/fuel/2023_fuel_fall.xlsx",
    "data/raw_data/fuel/2024_fuel_fall.xlsx",
    "data/raw_data/fuel/2025_fuel_fall.xlsx",
    "data/raw_data/fuel/2014_fuel_spring.xlsx",  
    "data/raw_data/fuel/2015_fuel_spring.xlsx",  
    "data/raw_data/fuel/2016_fuel_spring.xlsx",  
    "data/raw_data/fuel/2017_fuel_spring.xlsx",  
    "data/raw_data/fuel/2018_fuel_spring.xlsx",  
    "data/raw_data/fuel/2019_fuel_spring.xlsx",  
    "data/raw_data/fuel/2020_fuel_spring.xlsx",  
    "data/raw_data/fuel/2021_fuel_spring.xlsx",  
    "data/raw_data/fuel/2022_fuel_spring.xlsx",  
    "data/raw_data/fuel/2023_fuel_spring.xlsx",  
    "data/raw_data/fuel/2024_fuel_spring.xlsx",  
    "data/raw_data/fuel/2025_fuel_spring.xlsx",
    "data/raw_data/fuel/2026_fuel_spring.xlsx",
    "data/raw_data/fuel/2014_fuel_winter.xlsx",
    "data/raw_data/fuel/2015_fuel_winter.xlsx",
    "data/raw_data/fuel/2016_fuel_winter.xlsx",
    "data/raw_data/fuel/2017_fuel_winter.xlsx",
    "data/raw_data/fuel/2018_fuel_winter.xlsx",
    "data/raw_data/fuel/2019_fuel_winter.xlsx",
    "data/raw_data/fuel/2020_fuel_winter.xlsx",
    "data/raw_data/fuel/2021_fuel_winter.xlsx",
    "data/raw_data/fuel/2022_fuel_winter.xlsx",
    "data/raw_data/fuel/2023_fuel_winter.xlsx",
    "data/raw_data/fuel/2024_fuel_winter.xlsx",
    "data/raw_data/fuel/2025_fuel_winter.xlsx",
    "data/raw_data/fuel/2026_fuel_winter.xlsx",
    "data/raw_data/fuel/2014_fuel_summer.xlsx",
    "data/raw_data/fuel/2015_fuel_summer.xlsx",
    "data/raw_data/fuel/2016_fuel_summer.xlsx",
    "data/raw_data/fuel/2017_fuel_summer.xlsx",
    "data/raw_data/fuel/2018_fuel_summer.xlsx",
    "data/raw_data/fuel/2019_fuel_summer.xlsx",
    "data/raw_data/fuel/2020_fuel_summer.xlsx",
    "data/raw_data/fuel/2021_fuel_summer.xlsx",
    "data/raw_data/fuel/2022_fuel_summer.xlsx",
    "data/raw_data/fuel/2023_fuel_summer.xlsx",
    "data/raw_data/fuel/2024_fuel_summer.xlsx",
    "data/raw_data/fuel/2025_fuel_summer.xlsx",
    "data/raw_data/fuel/2026_fuel_summer.xlsx"
]

    
df = [dosya_temizle(dosya_oku(dosya)) for dosya in dosyalar]

def get_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    else:
        return "Fall"

for d in df:
    d["date"] = pd.to_datetime(d["date"], format="%d.%m.%Y")
    d["year"] = d["date"].dt.year
    d["month"] = d["date"].dt.month
    d["season"] = d["month"].apply(get_season)
    
    

all_fuel = pd.concat(df, ignore_index=True)
all_fuel["V/Pro Diesel"] = pd.to_numeric(all_fuel["V/Pro Diesel"], errors="coerce")
all_fuel["V/Max Diesel"] = pd.to_numeric(all_fuel["V/Max Diesel"], errors="coerce")

fuel_old = all_fuel[
    (all_fuel["year"] >= 2014) &
    (all_fuel["year"] < 2020)
]
fuel_new = all_fuel[
    all_fuel["year"] >= 2020
]


season_old = (
    fuel_old
    .groupby(["year", "season"], as_index=False)["V/Pro Diesel"]
    .mean()
    .round(2)
)

season_new = (
    fuel_new
    .groupby(["year", "season"], as_index=False)["V/Max Diesel"]
    .mean()
    .round(2)
)
season_old.rename(
    columns={"V/Pro Diesel": "diesel_Price"},
    inplace=True
)

season_new.rename(
    columns={"V/Max Diesel": "diesel_Price"},
    inplace=True
)
season_df = pd.concat(
    [season_old, season_new],
    ignore_index=True
)
print(season_df.info())
season_df.to_csv("data/processed/data_files/seasonal_fuel_prices.csv", index=False)
