import pandas as pd
from pathlib import Path

from app.database import SessionLocal
from app.models import Urun, Kota, Ilce

KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
KOTA_CSV_PATH = KOK_DIZIN / "data" / "processed" / "data_files" / "kota_sonuclari.csv"

kota_df = pd.read_csv(KOTA_CSV_PATH)

db = SessionLocal()

for i in range(len(kota_df)):
    ilce_adi = kota_df.loc[i, "district"]
    urun_adi = kota_df.loc[i, "product_name"]
    maksimum_kota = float(kota_df.loc[i, "2026 Kota"])

    urun = db.query(Urun).filter(Urun.urun_adi == urun_adi).first()
    if urun is None:
        print(urun_adi, "bulunamadı.")
        continue

    ilce = db.query(Ilce).filter(Ilce.ilce_adi == ilce_adi).first()
    if ilce is None:
        print(f"{ilce_adi} bulunamadı.")
        continue

    eski = db.query(Kota).filter(
        Kota.urun_id == urun.urun_id,
        Kota.ilce_id == ilce.ilce_id   # DÜZELTİLDİ: Ilce.ilce_id değil, ilce.ilce_id (bulunan kayıt)
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