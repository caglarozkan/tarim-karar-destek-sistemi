#OrtalamaUcret,MAL_ADI,BIRIM,ASGARI_FIYAT,AZAMI_FIYAT,MalId,tarih,HAL_TURU,MalTipId,MAL_TIPI,Gorsel,TARIH,ORTALAMA_FIYAT

import pandas as pd

df=pd.read_csv("data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari-2026.csv")
df=df.rename(columns={
    "ORTALAMA_FIYAT":"average_price",
    "MAL_ADI":"product_name",
    "BIRIM":"unit",
    "ASGARI_FIYAT":"min_price",
    "AZAMI_FIYAT":"max_price",
    "MalId":"product_id",
    "TARIH":"date",
}
)
df=df.drop(columns={ 'unit', 'product_id','OrtalamaUcret','tarih', 'HAL_TURU', 'MalTipId', 'MAL_TIPI', 'Gorsel'})
df.to_csv("data/processed/data_files/cleaned_2026.csv",index=False)
print(df.columns)