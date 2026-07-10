import pandas as pd

df = pd.read_csv(
    "data/raw_data/marketplace_data/izbb-sebzemeyve-hal-fiyatlari_2025.csv",
    encoding="cp1254",
    sep=";",
    engine="python"
)
df = df.copy()

bulten_satirlari = df[
    df.iloc[:, 0].astype(str).str.contains("Bülten Tarihi", na=False)
].index.tolist()

tum_bloklar = []

for i, satir_no in enumerate(bulten_satirlari):
    
    bulten_tarihi = df.iloc[satir_no, 4]
    mal_tipi = df.iloc[satir_no + 1, 4]
    
    veri_baslangic = satir_no + 4
    
    if i + 1 < len(bulten_satirlari):
        veri_bitis = bulten_satirlari[i + 1]
    else:
        veri_bitis = len(df)
    
    sol = df.iloc[veri_baslangic:veri_bitis, [0, 1, 5, 6, 8, 9]].copy()
    sol.columns = [
        "S_NO", "MAL_ADI", "BIRIM",
        "ASGARI_FIYAT", "AZAMI_UCRET", "ORTALAMA_UCRET"
    ]
    
    sag = df.iloc[veri_baslangic:veri_bitis, [11, 12, 14, 15, 16, 17]].copy()
    sag.columns = [
        "S_NO", "MAL_ADI", "BIRIM",
        "ASGARI_FIYAT", "AZAMI_UCRET", "ORTALAMA_UCRET"
    ]
    
    blok_df = pd.concat([sol, sag], ignore_index=True)
    
    blok_df["BULTEN_TARIHI"] = bulten_tarihi
    blok_df["MAL_TIPI"] = mal_tipi
    
    tum_bloklar.append(blok_df)

df_final = pd.concat(tum_bloklar, ignore_index=True)

df_final = df_final.dropna(how="all", subset=["S_NO", "MAL_ADI"])
df_final = df_final[df_final["MAL_ADI"].notna()]

df_final["S_NO"] = pd.to_numeric(df_final["S_NO"], errors="coerce")
df_final = df_final[df_final["S_NO"].notna()]

for col in ["ASGARI_FIYAT", "AZAMI_UCRET", "ORTALAMA_UCRET"]:
    df_final[col] = (
        df_final[col]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )
    df_final[col] = pd.to_numeric(df_final[col], errors="coerce")

# Kolon sırasını düzenle
df_final = df_final[[
    "BULTEN_TARIHI", "MAL_TIPI", "S_NO", "MAL_ADI",
    "BIRIM", "ASGARI_FIYAT", "AZAMI_UCRET", "ORTALAMA_UCRET"
]]

df_final = df_final.reset_index(drop=True)


print("=" * 80)
print(f"TOPLAM TEMİZ KAYIT SAYISI: {len(df_final)}")
print("=" * 80)
print(df_final.head(20))
print(df_final.tail(10))


df_final.to_csv(
    "data/processed/cleaned_2025.csv",
    index=False,
    encoding="utf-8-sig"
)
