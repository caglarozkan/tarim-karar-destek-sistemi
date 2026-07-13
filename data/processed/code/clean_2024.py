import pandas as pd
df=pd.read_csv("data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2024.csv")
df=df.drop(columns="_id")
df["TARIH"] = pd.to_datetime(df["TARIH"], errors="coerce")
df["TARIH"] = df["TARIH"].dt.strftime("%m/%d/%Y")
df.to_csv("data/processed/cleaned_2024.csv")