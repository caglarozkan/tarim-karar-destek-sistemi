import pandas as pd
import re

dosyalar = [
    "data/processed/data_files/cleaned_tuik.csv",
    "data/processed/data_files/cleaned_fertilizer.csv",
    "data/processed/data_files/seasonal_fuel_prices.csv"
]

tuik = pd.read_csv(dosyalar[0])
gubre = pd.read_csv(dosyalar[1])
petrol = pd.read_csv(dosyalar[2])

tuik.columns = tuik.columns.str.strip()
gubre.columns = gubre.columns.str.strip()
petrol.columns = petrol.columns.str.strip()

tuik = tuik.rename(columns={
    "ProductName": "product_name",
    "Year": "year",
    "District": "district",
    "Ekilen Alan": "planted_area",
    "Üretim Miktarı": "production_amount",
    "URUN_ADI": "product_name",
    "YIL": "year",
})

gubre = gubre.rename(columns={
    "Ortalama_Gubre_Maliyeti_Ton_TL": "fertilizer_price",
    "YIL": "year",
    "Year": "year",
})

petrol = petrol.rename(columns={
    "diesel_Price": "diesel_price",
    "FUEL_PRICE": "diesel_price",
    "YIL": "year",
    "Year": "year",
})

tuik["year"] = pd.to_numeric(tuik["year"], errors="coerce")
gubre["year"] = pd.to_numeric(gubre["year"], errors="coerce")
petrol["year"] = pd.to_numeric(petrol["year"], errors="coerce")

tuik = tuik[tuik["year"].notna()].copy()
gubre = gubre[gubre["year"].notna()].copy()
petrol = petrol[petrol["year"].notna()].copy()

tuik["year"] = tuik["year"].astype(int)
gubre["year"] = gubre["year"].astype(int)
petrol["year"] = petrol["year"].astype(int)

petrol["diesel_price"] = pd.to_numeric(
    petrol["diesel_price"],
    errors="coerce"
)

petrol_yearly = (
    petrol.groupby("year", as_index=False)["diesel_price"]
    .mean()
    .rename(columns={"diesel_price": "fuel_price"})
)

final = tuik.merge(
    petrol_yearly,
    on="year",
    how="left"
)

final = final.merge(
    gubre,
    on="year",
    how="left"
)


def clean_product_name(value):
    if pd.isna(value):
        return pd.NA

    value = str(value)

    value = value.replace("(", " ").replace(")", " ")

    value = (
        value
        .replace("İ", "I")
        .replace("ı", "I")
        .replace("Ş", "S")
        .replace("ş", "S")
        .replace("Ğ", "G")
        .replace("ğ", "G")
        .replace("Ü", "U")
        .replace("ü", "U")
        .replace("Ö", "O")
        .replace("ö", "O")
        .replace("Ç", "C")
        .replace("ç", "C")
        .replace(",", "")
    )

    value = value.upper()
    value = re.sub(r"\s+", " ", value)

    return value.strip()


PRODUCT_MAP = {
    "BAKLA TAZE": "BAKLA",
    "BEZELYE TAZE": "BEZELYE",
    "DOMATES SOFRALIK": "DOMATES SALKIM",
    "PATLICAN": "PATLICAN UZUN",
    "MARUL GOBEKLI": "MARUL",
    "KABAK SAKIZ": "KABAK TAZE",
    "HIYAR SOFRALIK": "SALATALIK SILOR",
}

final["product_name"] = final["product_name"].apply(clean_product_name)
final["product_name"] = final["product_name"].replace(PRODUCT_MAP)

final["planted_area"] = pd.to_numeric(
    final["planted_area"],
    errors="coerce"
)

final["production_amount"] = pd.to_numeric(
    final["production_amount"],
    errors="coerce"
)

if "fertilizer_price" in final.columns:
    final["fertilizer_price"] = pd.to_numeric(
        final["fertilizer_price"],
        errors="coerce"
    )

final = final.drop_duplicates().reset_index(drop=True)

final = final.drop(columns=["Amonyum_Sulfat","CAN","Ure","DAP","Gubre_20_20_0"]).reset_index(drop=True)
final.to_csv(
    "data/processed/data_files/final_risk_dataset.csv",
    index=False,
    encoding="utf-8-sig"
)
final=final.dropna()
print("final_risk_dataset.csv olusturuldu.")
print(final.head())