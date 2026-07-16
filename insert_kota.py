import pandas as pd
from database import SessionLocal
from models import Urun, Kota, Ilce

# Tahmin sonuçlarını okuma
kota_df = pd.read_csv("kota_sonuclari.csv")

db = SessionLocal()

for i in range(len(kota_df)):
    ilce_adi = kota_df.loc[i, "District"]
    urun_adi = kota_df.loc[i, "ProductName"]
    maksimum_kota = float(kota_df.loc[i, "2026 Kota"])

    #ürünü bul
    urun = db.query(Urun).filter(Urun.urun_adi == urun_adi).first()
    if urun is None:
        print(urun_adi, "bulunamadı.")
        continue

    # İlçeyi bul
    ilce = db.query(Ilce).filter(Ilce.ilce_adi == ilce_adi).first()
    if ilce is None:
        print(f"{ilce_adi} bulunamadı.")
        continue

    eski = db.query(Kota).filter(
        Kota.urun_id == urun.urun_id,
        Kota.ilce_id == Ilce.ilce_id
    ).first()

    if eski:
        eski.maksimum_kota = maksimum_kota

    else:
        yeni = Kota(
            urun_id=urun.urun_id,
            ilce_id=ilce.ilce_id,
            maksimum_kota=maksimum_kota,
            kullanilan_kota=0
        )
        db.add(yeni)

db.commit()
db.close()

print("Kota tablosu güncellendi.")