import pandas as pd
import re


dosya = "data/raw_data/tuik/tarimsal_urunler_son.csv"


df_raw = pd.read_csv(
    dosya,
    header=None,
    sep="|",
    engine="python",
    encoding="utf-8-sig"
)

df_raw = df_raw.dropna(axis=1, how="all")

desc_col = 1
year_col = 2

district_cols_names = [
    "İzmir(Bayındır)",
    "İzmir(Bergama)",
    "İzmir(Menderes)",
    "İzmir(Tire)",
    "İzmir(Torbalı)",
    "İzmir(Ödemiş)"
]

district_headers = df_raw.iloc[:, year_col:].copy()
district_headers = district_headers.dropna(how="all")

district_headers = district_headers.iloc[:, :len(district_cols_names) + 1]

district_headers.columns = ["Year"] + district_cols_names

district_headers["RawProduct"] = df_raw.loc[district_headers.index, desc_col]

district_headers["Year"] = pd.to_numeric(
    district_headers["Year"],
    errors="coerce"
)

district_headers = district_headers[
    district_headers["Year"].notna()
].copy()

district_headers["Year"] = district_headers["Year"].astype(int)

district_headers["block"] = (
    district_headers["Year"]
    .lt(district_headers["Year"].shift())
    .cumsum()
)

district_headers["RawProduct"] = (
    district_headers
    .groupby("block")["RawProduct"]
    .transform(lambda s: s.ffill().bfill())
)

product_parts = district_headers["RawProduct"].str.extract(
    r"^(?P<Metric>.*?)\s+ve\s+(?P<ProductCode>[\d.]+)\s+\((?P<ProductName>.*?)\)\s*-\s*(?P<Unit>.*)$"
)

district_headers = pd.concat([district_headers, product_parts], axis=1)

district_cols = [
    col for col in district_headers.columns
    if isinstance(col, str) and col.startswith("İzmir(")
]

df_long = district_headers.melt(
    id_vars=["Metric", "ProductCode", "ProductName", "Unit", "Year"],
    value_vars=district_cols,
    var_name="District",
    value_name="Value"
)

df_long = df_long.drop(columns=["ProductCode"])

df_long["Value"] = pd.to_numeric(
    df_long["Value"],
    errors="coerce"
)

df_long = df_long.sort_values(
    by=["ProductName", "Year", "District"]
).reset_index(drop=True)

df_long = df_long.pivot_table(
    index=["ProductName", "Year", "District"],
    columns="Metric",
    values="Value",
    aggfunc="first"
).reset_index()

df_long.columns.name = None

df_long = df_long.rename(columns={
    "ProductName": "product_name",
    "Year": "year",
    "District": "district",
    "Ekilen Alan": "planted_area",
    "Üretim": "production_amount",
    "Üretim Miktarı": "production_amount"
})


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
    "SOGAN KURU": "SOGAN KURU",
    "BIBER SIVRI": "BIBER SIVRI",
}

ALLOWED_PRODUCTS = [
    "BAKLA",
    "BEZELYE",
    "DOMATES SALKIM",
    "PATLICAN UZUN",
    "MARUL",
    "LAHANA KIRMIZI",
    "LAHANA BEYAZ",
    "PIRASA",
    "SALATALIK SILOR",
    "SOGAN KURU",
    "KARPUZ",
    "KARNABAHAR",
    "KABAK TAZE",
    "ISPANAK",
    "BROKOLI",
    "BIBER SIVRI"
]

df_long["product_name"] = df_long["product_name"].apply(clean_product_name)
df_long["product_name"] = df_long["product_name"].replace(PRODUCT_MAP)

df_long = df_long[
    df_long["product_name"].isin(ALLOWED_PRODUCTS)
]

df_long["year"] = pd.to_numeric(df_long["year"], errors="coerce")
df_long["planted_area"] = pd.to_numeric(df_long["planted_area"], errors="coerce")

if "production_amount" in df_long.columns:
    df_long["production_amount"] = pd.to_numeric(
        df_long["production_amount"],
        errors="coerce"
    )

df_long = df_long.dropna(
    subset=["product_name", "year", "district"]
)

df_long["year"] = df_long["year"].astype(int)

df_long = df_long.reset_index(drop=True)

df_long.to_csv(
    "data/processed/data_files/cleaned_tuik.csv",
    index=False,
    encoding="utf-8-sig"
)

print("cleaned_tuik.csv oluşturuldu.")
print(df_long.head())