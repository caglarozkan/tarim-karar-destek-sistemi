import pandas as pd
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# Proje kökü: scripts -> app -> root (3 seviye yukarı, sonra data/'ya iniyor)
KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
GIRIS_PATH = KOK_DIZIN / "data" / "processed" / "data_files" / "cleaned_tuik.csv"
CIKIS_PATH = KOK_DIZIN / "data" / "processed" / "data_files" / "kota_sonuclari.csv"

df = pd.read_csv(GIRIS_PATH)

print(df.head())
print(df.isnull().sum())

df["District"] = df["District"].str.replace("İzmir(", "", regex=False)
df["District"] = df["District"].str.replace(")", "", regex=False)

# ekilen alan eksik olan değerleri ortalama ile doldurma
for i in range(len(df)):
    if pd.isnull(df.loc[i, "Ekilen Alan"]):
        urun = df.loc[i, "ProductName"]
        ilce = df.loc[i, "District"]

        if urun != "Soğan (Kuru)":
            filtre = (df["ProductName"] == urun) & (df["District"] == ilce)
            ortalama = df.loc[filtre, "Ekilen Alan"].mean()
            df.loc[i, "Ekilen Alan"] = ortalama

# üretim miktarı eksik olan yerleri ortalama ile doldurma
for i in range(len(df)):
    if pd.isnull(df.loc[i, "Üretim Miktarı"]):
        urun = df.loc[i, "ProductName"]
        ilce = df.loc[i, "District"]

        if urun != "Soğan (Kuru)":
            filtre = (df["ProductName"] == urun) & (df["District"] == ilce)
            ortalama = df.loc[filtre, "Üretim Miktarı"].mean()
            df.loc[i, "Üretim Miktarı"] = ortalama

print(df.isnull().sum())

egitim = df.dropna(subset=["Ekilen Alan"]).copy()
egitim = pd.get_dummies(egitim, columns=["District", "ProductName"])

X = egitim.drop(columns=["Unnamed: 0", "Ekilen Alan", "Üretim Miktarı"])
y = egitim["Ekilen Alan"]

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)

from sklearn.linear_model import LinearRegression
linear = LinearRegression()
linear.fit(X_train, y_train)
linear_predict = linear.predict(X_test)

from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
print("\n-- Linear Regression --")
print("R2 :", r2_score(y_test, linear_predict))
print("MAE :", mean_absolute_error(y_test, linear_predict))
print("MSE :", mean_squared_error(y_test, linear_predict))

from sklearn.ensemble import RandomForestRegressor
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_predict = rf.predict(X_test)
print("\n-- Random Forest --")
print("R2 :", r2_score(y_test, rf_predict))
print("MAE :", mean_absolute_error(y_test, rf_predict))
print("MSE :", mean_squared_error(y_test, rf_predict))

# her ürün-ilçe için kota bilgisi
kota_df = pd.DataFrame(columns=["District", "ProductName", "2026 Kota"])
ilceler = df["District"].unique()
urunler = df["ProductName"].unique()

for ilce in ilceler:
    for urun in urunler:
        veri = df[(df["District"] == ilce) & (df["ProductName"] == urun)]
        veri = veri.dropna(subset=["Ekilen Alan"])

        if len(veri) < 2:
            kota_df.loc[len(kota_df)] = [ilce, urun, 0]
            continue

        X = veri[["Year"]]
        y = veri["Ekilen Alan"]

        model = RandomForestRegressor(n_estimators=50, random_state=42)
        model.fit(X, y)
        predict = model.predict([[2026]])

        kota_df.loc[len(kota_df)] = [ilce, urun, round(predict[0], 2)]

print("2026 KOTA TAHMİNLERİ")
print(kota_df)

kota_df.to_csv(CIKIS_PATH, index=False)
print(f"Kota tahminleri oluşturuldu: {CIKIS_PATH}")