import pandas as pd
import warnings
from pathlib import Path

warnings.filterwarnings('ignore')

# Proje kökü: scripts -> app -> root (3 seviye yukarı, sonra data/'ya iniyor)
KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
GIRIS_PATH = KOK_DIZIN / "data" / "processed" / "data_files" / "cleaned_tuik.csv"
CIKIS_PATH = KOK_DIZIN / "data" / "processed" / "data_files" / "üretim_miktari_sonuclari.csv"

df = pd.read_csv(GIRIS_PATH)

print(df.head())
print(df.isnull().sum())

df["district"] = df["district"].str.replace("İzmir(", "", regex=False)
df["district"] = df["district"].str.replace(")", "", regex=False)

# üretim miktarı eksik olan yerleri ortalama ile doldurma
for i in range(len(df)):
    if pd.isnull(df.loc[i, "Üretim Miktarı"]):
        urun = df.loc[i, "product_name"]
        ilce = df.loc[i, "district"]

        if urun != "SOGAN KURU":
            filtre = (df["product_name"] == urun) & (df["district"] == ilce)
            ortalama = df.loc[filtre, "Üretim Miktarı"].mean()
            df.loc[i, "Üretim Miktarı"] = ortalama

print(df.isnull().sum())

egitim = df.dropna(subset=["Üretim Miktarı"]).copy()
egitim = pd.get_dummies(egitim, columns=["district", "product_name"])

X = egitim.drop(columns=["planted_area","Üretim Miktarı"])
y = egitim["Üretim Miktarı"]

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

# hyperparameter tuning
params = {
    "n_estimators": [200,300,500],
    "max_depth": [1, 3, 5, 10],
    "criterion": ["squared_error","absolute_error","poisson"]
}
from sklearn.model_selection import GridSearchCV

from sklearn.ensemble import RandomForestRegressor
rf = RandomForestRegressor(n_estimators=100, random_state=42)
rf.fit(X_train, y_train)
rf_predict = rf.predict(X_test)
print("\n-- Random Forest --")
print("R2 :", r2_score(y_test, rf_predict))
print("MAE :", mean_absolute_error(y_test, rf_predict))
print("MSE :", mean_squared_error(y_test, rf_predict))

#rf hyperparameter
grid_rf=GridSearchCV(
    estimator=RandomForestRegressor(),
    param_grid=params,
    n_jobs=-1
)
grid_rf.fit(X_train, y_train)
grid_rf_predict = grid_rf.predict(X_test)
print("best params:",grid_rf.best_params_)
print("\n-- Random Forest after --")
print("R2 :", r2_score(y_test, grid_rf_predict))
print("MAE :", mean_absolute_error(y_test, grid_rf_predict))
print("MSE :", mean_squared_error(y_test, grid_rf_predict))


#xgbregressor deneme
from xgboost import XGBRegressor
xgbr=XGBRegressor()
xgbr.fit(X_train, y_train)
xgbr_predict=xgbr.predict(X_test)
print("\n-- XGB Regression --")
print("R2 :", r2_score(y_test, rf_predict))
print("MAE :", mean_absolute_error(y_test, xgbr_predict))
print("MSE :", mean_squared_error(y_test, xgbr_predict))

params = {
    "n_estimators":[200,300,500],
    "learning_rate":[0.01,0.05,0.1],
    "max_depth":[3,5,7],
    "subsample":[0.7,0.8,1],
    "colsample_bytree":[0.7,0.8,1]
}
#xgbr
grid = GridSearchCV(
    estimator=XGBRegressor(),
    param_grid=params,
    n_jobs=-1,
    cv=5
)
grid.fit(X_train, y_train)
grid_predict = grid.predict(X_test)
print("best PARAM:",grid.best_params_)
print("\n-- XGBoost Regression hyperparameter --")
print("R2:",r2_score(y_test, grid_predict))
print("MAE :", mean_absolute_error(y_test, grid_predict))
print("MSE :",mean_squared_error(y_test, grid_predict))
# !best PARAM: {'colsample_bytree': 1, 'learning_rate': 0.05, 'max_depth': 7, 'n_estimators': 500, 'subsample': 0.7}
"""
-- XGBoost Regression hyperparameter --
R2: 0.9072217935620391
MAE : 1675.2474792895064
MSE : 22793926.982764017
"""

# her ürün-ilçe için kota bilgisi
kota_df = pd.DataFrame(columns=["district", "product_name", "2026 Üretim Miktari"])
ilceler = df["district"].unique()
urunler = df["product_name"].unique()

for ilce in ilceler:
    for urun in urunler:
        veri = df[(df["district"] == ilce) & (df["product_name"] == urun)]
        veri = veri.dropna(subset=["Üretim Miktarı"])

        if len(veri) < 2:
            kota_df.loc[len(kota_df)] = [ilce, urun, 0]
            continue

        X = veri[["year"]]
        y = veri["Üretim Miktarı"]

        model = XGBRegressor(n_estimators=500,colsample_bytree=1,learning_rate=0.05, random_state=42)
        model.fit(X, y)
        predict = model.predict([[2026]])

        kota_df.loc[len(kota_df)] = [ilce, urun, round(predict[0], 2)]

print("2026 Üretim TAHMİNLERİ")
print(kota_df)

kota_df.to_csv(CIKIS_PATH, index=False)
print(f"Üretim Miktarı tahminleri oluşturuldu: {CIKIS_PATH}")