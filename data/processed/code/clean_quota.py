import pandas as pd


INPUT_PATH = "data/processed/data_files/kota_sonuclari.csv"
OUTPUT_PATH = "data/processed/data_files/cleaned_quota.csv"


PRODUCT_NAME_MAP = {
    "Biber (Sivri)": "BIBER SIVRI",
    "Domates (Sofralık)": "DOMATES SALKIM",
    "Hıyar (Sofralık)": "SALATALIK SILOR",
    "Kabak (Sakız)": "KABAK TAZE",
    "Soğan (Kuru)": "SOGAN KURU",
    "Patlıcan": "PATLICAN",
    "Karpuz": "KARPUZ",
}


kota = pd.read_csv(INPUT_PATH)

kota = kota.rename(columns={
    "District": "district",
    "ProductName": "product_name",
    "2026 Kota": "quota"
})

kota["year"] = 2026

kota["district"] = kota["district"].astype(str).str.strip()

kota["product_name"] = (
    kota["product_name"]
    .astype(str)
    .str.strip()
    .replace(PRODUCT_NAME_MAP)
)

kota["quota"] = pd.to_numeric(
    kota["quota"],
    errors="coerce"
)

kota = kota[
    [
        "year",
        "district",
        "product_name",
        "quota"
    ]
]

kota.to_csv(OUTPUT_PATH, index=False)

print("Duzenlenmis kota dosyasi olusturuldu:")
print(OUTPUT_PATH)
print(kota.head(20))