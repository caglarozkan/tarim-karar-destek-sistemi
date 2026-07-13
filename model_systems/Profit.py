import pandas as pd
import numpy as np

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

da = pd.read_csv("data/processed/data_files/final_price_dataset.csv")
df = da.copy()

df = df.dropna(subset=["URUN_ADI", "YIL", "SEZON", "ORTALAMA_FIYAT"])

df["URUN_ADI"] = df["URUN_ADI"].astype(str).str.strip().str.upper()
df["SEZON"] = df["SEZON"].astype(str).str.strip()
df["YIL"] = pd.to_numeric(df["YIL"], errors="coerce")
df["ORTALAMA_FIYAT"] = pd.to_numeric(df["ORTALAMA_FIYAT"], errors="coerce")

df=df.dropna(subset=["YIL", "ORTALAMA_FIYAT"])

X=df[["URUN_ADI","YIL","SEZON"]]
y=df["ORTALAMA_FIYAT"]

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

categorical_features=["URUN_ADI","SEZON"]
numeric_features=["YIL"]

preprocessor=ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), categorical_features),
        ("num", "passthrough", numeric_features)
    ]
)

model=Pipeline(
    steps=[
        ("preprocessor", preprocessor),
        ("regressor", RandomForestRegressor(
            n_estimators=300,
            random_state=42,
            max_depth=None,
            min_samples_split=2,
            min_samples_leaf=1,
            n_jobs=-1
        ))
    ]
)

model.fit(X_train, y_train)

y_pred=model.predict(X_test)

mae=mean_absolute_error(y_test, y_pred)
rmse=np.sqrt(mean_squared_error(y_test, y_pred))
r2=r2_score(y_test, y_pred)

print("Model Performansı")
print("MAE :", mae)
print("RMSE:", rmse)
print("R2  :", r2)
