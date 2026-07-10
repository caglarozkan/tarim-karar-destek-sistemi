import pandas as pd
df=pd.read_csv("data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2024.csv")
df=df.drop(columns="_id")
df.to_csv("data/processed/cleaned_2024.csv")