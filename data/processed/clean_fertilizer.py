import pandas as pd 
import numpy as np 

df=pd.read_csv("data/raw_data/fertilizer/gübre.csv",sep=";",encoding="ISO-8859-1")

df.columns = [
    "YIL",
    "Amonyum_Sulfat",
    "CAN",
    "Ure",
    "DAP",
    "Gubre_20_20_0"
]
df=df.drop(index=[0,1])

            
def clean_price(value):
    value = str(value).strip()
    value = value.replace(".", "")   # binlik noktayı sil
    value = value.replace(",", ".")  # varsa virgülü ondalığa çevir
    return float(value)

price_columns = [
    "Amonyum_Sulfat",
    "CAN",
    "Ure",
    "DAP",
    "Gubre_20_20_0"
]

for col in price_columns:
    df[col] = df[col].apply(clean_price)
    
df["Ortalama_Gubre_Maliyeti(Ton/TL)"] = (
    df[["Amonyum_Sulfat", "CAN", "Ure"]].mean(axis=1)
).round(2)

df["YIL"] = df["YIL"].replace({"2021 (1. Yar?)": "2021 (1. Yari)","2021 (2. Yar?)": "2021 (2. Yari)"})
print(df.tail(10))
df.to_csv("data/processed/cleaned_fertilizer.csv",index=False)