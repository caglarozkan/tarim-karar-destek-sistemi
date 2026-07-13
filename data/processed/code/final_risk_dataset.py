import pandas as pd

dosyalar = [
    "data/processed/data_files/cleaned_tuik.csv",
    "data/processed/data_files/cleaned_fertilizer.csv",
    "data/processed/data_files/seasonal_fuel_prices.csv"
]

# Dosyaları oku
tuik = pd.read_csv(dosyalar[0])
gubre = pd.read_csv(dosyalar[1])
petrol = pd.read_csv(dosyalar[2])

# Kolon isimlerindeki baştaki/sondaki boşlukları temizle
tuik.columns = tuik.columns.str.strip()
gubre.columns = gubre.columns.str.strip()
petrol.columns = petrol.columns.str.strip()

# Year sütunlarını aynı tipe çevir
tuik["Year"] = pd.to_numeric(tuik["Year"], errors="coerce").astype(int)
gubre["Year"] = pd.to_numeric(gubre["Year"], errors="coerce").astype(int)
petrol["Year"] = pd.to_numeric(petrol["Year"], errors="coerce").astype(int)

# Mazot fiyatını yıllık ortalamaya çevir
petrol_yearly = (
    petrol.groupby("Year", as_index=False)["Diesel_Price"]
    .mean()
    .rename(columns={"Diesel_Price": "FUEL_PRICE"})
)

# Gübre tablosundan gerekli kolonları al
gubre1 = (
    gubre[["Year", "Ortalama_Gubre_Maliyeti_Ton_TL"]]
    .rename(columns={
        "Ortalama_Gubre_Maliyeti(Ton/TL)": "FERTILIZER_PRICE"
    })
)

# Merge işlemleri
final = tuik.merge(
    petrol_yearly,
    on="Year",
    how="left"
)

final = final.merge(
    gubre1,
    on="Year",
    how="left"
)
final=final.iloc[:,1:]
final = final.rename(columns={
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
final.to_csv("data/processed/data_files/final_risk_dataset.csv")