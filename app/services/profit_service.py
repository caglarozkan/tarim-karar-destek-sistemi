from pathlib import Path
import pandas as pd

from app import models
from app.services.price_prediction import predict_product_price
from app.services.fuel_service import predict_fuel_price
from app.services.fertilizer_service import get_commodity_price

# Bu dosyanin bulundugu yerden proje kokune cikip data klasorune iniyoruz
KOK_DIZIN = Path(__file__).resolve().parent.parent.parent
URETIM_TAHMIN_PATH = KOK_DIZIN / "data" / "processed" / "data_files" / "üretim_miktari_sonuclari.csv"

#orman bakanlıgı pdfe göre
GUBRE_RECETESI = {
    "DOMATES SALKIM": {"azot_kg": 14, "fosfor_kg": 10},
    "BIBER SIVRI":      {"azot_kg": 14, "fosfor_kg": 10},
    "SALATALIK SILOR":   {"azot_kg": 14, "fosfor_kg": 10},
    "KABAK TAZE":      {"azot_kg": 14, "fosfor_kg": 10},
    "PATLICAN UZUN":           {"azot_kg": 14, "fosfor_kg": 10},
    "SOGAN KURU":       {"azot_kg": 13, "fosfor_kg": 9},
    "KARPUZ":             {"azot_kg": 15, "fosfor_kg": 9},
    "BAKLA": {"azot_kg": 15, "fosfor_kg": 9},
    "BEZELYE": {"azot_kg": 15, "fosfor_kg": 9},
    "BROKOLI": {"azot_kg": 15, "fosfor_kg": 9},
    "ISPANAK": {"azot_kg": 15, "fosfor_kg": 9},
    "KARNABAHAR": {"azot_kg": 15, "fosfor_kg": 9},
    "LAHANA BEYAZ": {"azot_kg": 15, "fosfor_kg": 9},
    "LAHANA KIRMIZI": {"azot_kg": 15, "fosfor_kg": 9},
    "MARUL":{"azot_kg": 15, "fosfor_kg": 9},
    "PIRASA": {"azot_kg": 15, "fosfor_kg": 9},
}

# Saf maddeyi gercek gubre urunune cevirmek icin carpanlar (PDF'ten)
# Ornek: 14 kg saf azot lazimsa, Ure gubresi olarak 14 x 2.2 = 30.8 kg Ure almamiz lazim
UREYE_CEVIRME_CARPANI = 2.2
DAP_A_CEVIRME_CARPANI = 2.2


# Sadece Domates icin net veri var, digerleri icin ayni oran kullanildi (yaklasik)
MAZOT_TUKETIMI_LITRE_DONUM = {
    "DOMATES SALKIM": 16.98,
    "BIBER SIVRI":      16.98,
    "SALATALIK SILOR":   16.98,
    "KABAK TAZE":      16.98,
    "PATLICAN":           16.98,
    "SOGAN KURU":       16.98,
    "KARPUZ":             16.98,
    "BAKLA":             16.98,
    "BEZELYE":             16.98,
    "BROKOLI":             16.98,
    "ISPANAK":             16.98,
    "KARNABAHAR":             16.98,
    "LAHANA BEYAZ":             16.98,
    "LAHANA KIRMIZI":             16.98,
    "MARUL":             16.98,
    "PIRASA":             16.98,
}

def uretim_tahmin_haritasi_olustur():
    df = pd.read_csv(URETIM_TAHMIN_PATH)

    harita = {}
    for i in range(len(df)):
        ilce = df.loc[i, "district"]
        urun = df.loc[i, "product_name"]
        tahmini_uretim = df.loc[i, "2026 Üretim Miktari"]
        harita[(ilce, urun)] = tahmini_uretim
    return harita

# Uygulama baslarken bir kez olusturulur
URETIM_TAHMIN_HARITASI = uretim_tahmin_haritasi_olustur()

#verim orani = tahmini uretim / tahmini ekilen
def verim_orani_hesapla(ilce_id, urun_id, ilce_adi, urun_adi_csv, db):
    kota_kaydi = db.query(models.Kota).filter(
        models.Kota.ilce_id == ilce_id,
        models.Kota.urun_id == urun_id
    ).first()

    if kota_kaydi is None or kota_kaydi.maksimum_kota is None or kota_kaydi.maksimum_kota <= 0: #db kontrlü
        raise ValueError("Bu ilce/urun icin tahmini ekilen alan verisi bulunamadi.")

    anahtar = (ilce_adi, urun_adi_csv)
    tahmini_uretim = URETIM_TAHMIN_HARITASI.get(anahtar)
    print("Anahtar:", anahtar)
    print("Tahmini üretim:", tahmini_uretim)
    print("Maksimum kota:", kota_kaydi.maksimum_kota)

    if tahmini_uretim is None or tahmini_uretim <= 0:
        raise ValueError("Bu ilce/urun icin tahmini uretim verisi bulunamadi.")

    verim_orani = tahmini_uretim / kota_kaydi.maksimum_kota
    return verim_orani


def tahmini_gelir_hesapla(donum, verim_orani, tahmini_fiyat):
    tahmini_uretim = donum * verim_orani #kullanıcıdan alınan
    tahmini_gelir = tahmini_uretim * 1000 * tahmini_fiyat #tahmini fiyat modelden gelen kg->ton dönüşümü

    return {
        "tahmini_uretim": round(tahmini_uretim, 2),
        "tahmini_gelir": round(tahmini_gelir, 2),
    }


def gubre_gideri_hesapla(urun, donum, gubre_fiyati_ton_basi):
    recete = GUBRE_RECETESI.get(urun)
    if recete is None:
        raise ValueError(f"{urun} icin gubre recetesi tanimli degil.")

    #ürün için gerekli olan saf azotu bulma
    saf_azot_kg = recete["azot_kg"] * donum
    saf_fosfor_kg = recete["fosfor_kg"] * donum

    #gerekli olan saf azot ve fosfora ulaşmak için gerekli olan üre miktarı ve dap miktarını bulma
    ure_miktari_kg = saf_azot_kg * UREYE_CEVIRME_CARPANI
    dap_miktari_kg = saf_fosfor_kg * DAP_A_CEVIRME_CARPANI

    toplam_gubre_kg = ure_miktari_kg + dap_miktari_kg

    # 3. adim: kg'i tona cevir (fiyat ton bazinda oldugu icin)
    toplam_gubre_ton = toplam_gubre_kg / 1000

    # 4. adim: ton miktarini fiyatla carp, TL gideri bul
    gubre_gideri = toplam_gubre_ton * gubre_fiyati_ton_basi

    return round(gubre_gideri, 2)


def mazot_gideri_hesapla(urun, donum, mazot_fiyati_litre_basi):
    tuketim_litre_donum = MAZOT_TUKETIMI_LITRE_DONUM.get(urun)
    if tuketim_litre_donum is None:
        raise ValueError(f"{urun} icin mazot tuketim verisi tanimli degil.")

    toplam_litre = tuketim_litre_donum * donum
    mazot_gideri = toplam_litre * mazot_fiyati_litre_basi

    return round(mazot_gideri, 2)


def tahmini_gider_hesapla(urun, donum, gubre_fiyati_ton_basi, mazot_fiyati_litre_basi,
                           sulama_maliyeti, iscilik_maliyeti, tohum_maliyeti):
    gubre_gideri = gubre_gideri_hesapla(urun, donum, gubre_fiyati_ton_basi)
    mazot_gideri = mazot_gideri_hesapla(urun, donum, mazot_fiyati_litre_basi)

    # opsiyonel maliyetleri toplama
    ek_giderler = 0
    if sulama_maliyeti:
        ek_giderler = ek_giderler + sulama_maliyeti
    if iscilik_maliyeti:
        ek_giderler = ek_giderler + iscilik_maliyeti
    if tohum_maliyeti:
        ek_giderler = ek_giderler + tohum_maliyeti

    toplam_gider = gubre_gideri + mazot_gideri + ek_giderler

    return {
        "gubre_gideri": gubre_gideri,
        "mazot_gideri": mazot_gideri,
        "ek_giderler": round(ek_giderler, 2),
        "toplam_gider": round(toplam_gider, 2),
    }


def net_kar_hesapla(tahmini_gelir, toplam_gider):
    return round(tahmini_gelir - toplam_gider, 2)

#fiyat tahmini modelini cagırıyor
def tahmini_fiyat_al(urun_adi_csv, hedef_yil, hedef_sezon):
    sonuc = predict_product_price(
        product_name=urun_adi_csv,
        target_year=hedef_yil,
        target_season=hedef_sezon,
    )
    return sonuc["predicted_price"]


def guncel_gubre_fiyati_al():
    return get_commodity_price("urea")

#mazot tahmin modelini cagırıyor
def tahmini_mazot_fiyati_al(hedef_yil, hedef_sezon):
    return predict_fuel_price(hedef_yil, hedef_sezon)


def kar_hesapla_tam(db, ilce_id, urun_id, ilce_adi, urun_sistem_adi, urun_adi_csv,
                     donum, hedef_yil, hedef_sezon,
                     sulama_maliyeti, iscilik_maliyeti, tohum_maliyeti):
    # 1. adim: verim oranini bul
    verim_orani = verim_orani_hesapla(ilce_id, urun_id, ilce_adi, urun_adi_csv, db)

    # 2. adim: tahmini fiyati al
    tahmini_fiyat = tahmini_fiyat_al(urun_adi_csv, hedef_yil, hedef_sezon)

    # 3. adim: gelir hesapla
    gelir_sonucu = tahmini_gelir_hesapla(donum, verim_orani, tahmini_fiyat)

    # 4. adim: gubre ve mazot fiyatlarini al
    gubre_fiyati_ton_basi = guncel_gubre_fiyati_al()
    mazot_fiyati_litre_basi = tahmini_mazot_fiyati_al(hedef_yil, hedef_sezon)

    # 5. adim: gider hesapla
    gider_sonucu = tahmini_gider_hesapla(
        urun_sistem_adi, donum, gubre_fiyati_ton_basi, mazot_fiyati_litre_basi,
        sulama_maliyeti, iscilik_maliyeti, tohum_maliyeti
    )

    # 6. adim: net kar
    net_kar = net_kar_hesapla(gelir_sonucu["tahmini_gelir"], gider_sonucu["toplam_gider"])

    print("\n========== KAR HESABI ==========")
    print("İlçe:", ilce_adi)
    print("Ürün:", urun_adi_csv)
    print("Dönüm:", donum)
    print("Verim Oranı:", verim_orani)
    print("Tahmini Fiyat:", tahmini_fiyat)
    print("Tahmini Üretim:", gelir_sonucu["tahmini_uretim"])
    print("Tahmini Gelir:", gelir_sonucu["tahmini_gelir"])
    print("================================\n")

    print("Gübre gideri:", gider_sonucu["gubre_gideri"])
    print("Mazot gideri:", gider_sonucu["mazot_gideri"])
    print("Ek giderler:", gider_sonucu["ek_giderler"])
    print("Toplam gider:", gider_sonucu["toplam_gider"])

    # hepsini tek bir sozlukte birlestir
    sonuc = {
        "tahmini_uretim": gelir_sonucu["tahmini_uretim"],
        "tahmini_fiyat": tahmini_fiyat,
        "tahmini_gelir": gelir_sonucu["tahmini_gelir"],
        "gubre_gideri": gider_sonucu["gubre_gideri"],
        "mazot_gideri": gider_sonucu["mazot_gideri"],
        "ek_giderler": gider_sonucu["ek_giderler"],
        "toplam_gider": gider_sonucu["toplam_gider"],
        "net_kar": net_kar,
    }
    return sonuc