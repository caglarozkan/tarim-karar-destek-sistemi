import pandas as pd 
import re
import pandas as pd

dosya="data/raw_data/tuik/tarimsal_urunler.xls"
df_raw = pd.read_excel(dosya, header=None)

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

# Örnek metin:
# Ekilen Alan ve 01.13.21.00.00. (Karpuz) - Dekar
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
df_long=df_long.drop(columns=["ProductCode"])
df_long = df_long.sort_values(
    by=["ProductName", "Year", "District"]
).reset_index(drop=True)

df_long.to_csv("data/processed/clean_tuik.csv", index=False)