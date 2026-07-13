from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models
import schemas
from database import SessionLocal

# İşlem yollarını ayıran Router objemiz
router = APIRouter()

# Şifreleri hash'lemek ve kontrol etmek için güvenli mekanizma
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Her işlemde veritabanı tüneli açıp kapatan fonksiyon
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#KULLANICI KAYIT ENDPOINT i
@router.post("/kullanici/kayit",response_model=schemas.KullaniciResponse)

def kullanici_kayit(kullanici:schemas.KullaniciCreate,db:Session=Depends(get_db)):

    kontrol=db.query(models.Kullanici).filter(models.Kullanici.email==kullanici.email).first()

    if kontrol:
        raise HTTPException(
            status_code=400,
            detail="Bu email zaten kayıtlı."
        )

    yeni=models.Kullanici(
        ad_soyad=kullanici.ad_soyad,
        email=kullanici.email,
        sifre_hash=get_password_hash(kullanici.sifre),
        yas=kullanici.yas,
        cinsiyet=kullanici.cinsiyet,
        telefon=kullanici.telefon

    )

    db.add(yeni)
    db.commit()
    db.refresh(yeni)
    return yeni


#KULLANICI GİRİŞ ENDPOINT i
@router.post("/kullanici/giris")

def giris(kullanici:schemas.KullaniciLogin,db:Session=Depends(get_db)):

    dbUser=db.query(models.Kullanici).filter(models.Kullanici.email==kullanici.email).first()

    if not dbUser:
        raise HTTPException(
            status_code=401,
            detail="Email veya şifre yanlış."
        )

    if not verify_password(kullanici.sifre,dbUser.sifre_hash):
        raise HTTPException(
            status_code=401,
            detail="Email veya şifre yanlış."
        )

    log=models.KullaniciAktiviteLog(
        kullanici_id=dbUser.kullanici_id,
        islem_tipi="Giriş Yapıldı"

    )
    db.add(log)
    db.commit()

    return{
          "kullanici_id": dbUser.kullanici_id,
          "ad_soyad": dbUser.ad_soyad,
          "yas": dbUser.yas,
          "cinsiyet": dbUser.cinsiyet,
          "telefon": dbUser.telefon

    }

#kullanıcı bilgilerini getirir
@router.get("/kullanici/{kullanici_id}")

def kullanici_getir(kullanici_id:int,db:Session=Depends(get_db)):

    user=db.query(models.Kullanici).filter(models.Kullanici.kullanici_id==kullanici_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Kullanıcı bulunamadı."
        )

    return{
        "ad":user.ad_soyad,
        "email":user.email,
        "yas":user.yas,
        "cinsiyet":user.cinsiyet,
        "telefon":user.telefon
    }


#kullanıcı bilgilerini günceller ( kişisel bilgilerim sayfasından)
@router.put("/kullanici/guncelle")

def kullanici_guncelle(veri:schemas.KullaniciUpdate,db:Session=Depends(get_db)):
    user=db.query(models.Kullanici).filter(models.Kullanici.kullanici_id==veri.kullanici_id).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="Kullanıcı bulunamadı."
        )

    user.ad_soyad=veri.ad_soyad
    user.yas=veri.yas
    user.cinsiyet=veri.cinsiyet
    user.telefon=veri.telefon

    db.commit()

    return{
        "mesaj":"Bilgiler güncellendi."
    }

"""
# ==========================================
# 3. TARLA EKLEME (Kullanıcı ID'sine göre Tarla ekler, otomatik tarla_id üretir)
# ==========================================
@router.post("/tarla/ekle", response_model=schemas.TarlaResponse)
def tarla_ekle(tarla: schemas.TarlaCreate, aktif_kullanici_id: int, db: Session = Depends(get_db)):
    yeni_tarla = models.Tarla(
        kullanici_id=aktif_kullanici_id,
        tarla_adi=tarla.tarla_adi,
        toplam_donum=tarla.toplam_donum,
        ilce=tarla.ilce
    )
    db.add(yeni_tarla)
    #db.commit()
    #db.refresh(yeni_tarla)  # Otomatik üretilen tarla_id'yi alır
    return yeni_tarla
"""

"""# ==========================================
# 4. RİSK ANALİZİ LOG KAYDI (Hesaplanan verileri DB'ye zımbalar)
# ==========================================
@router.post("/risk-analiz/log")
def risk_analiz_log_kaydet(sorgu: schemas.RiskAnalizRequest, kullanici_id: int, hesaplanan_risk: float,
                           db: Session = Depends(get_db)):
    yeni_log = models.RiskAnalizLog(
        kullanici_id=kullanici_id,
        sorgulanan_ilce=sorgu.sorgulanan_ilce,
        urun_id=sorgu.urun_id,
        girilen_donum=sorgu.girilen_donum,
        donen_risk_orani=hesaplanan_risk
    )
    db.add(yeni_log)
    # db.commit()
    return {"mesaj": "Risk analizi verileri başarıyla loglandı."}
"""

""" ==========================================
# 5. KOTA BİLGİSİ GETİRME (Dinamik İlçe ve Ürün Sorgusu)
# ==========================================
@router.get("/kota/durum")
def kota_durumunu_getir(gelen_ilce: str, gelen_urun_id: int, db: Session = Depends(get_db)):

    kota_sorgusu = db.query(models.Kota).filter(
        models.Kota.ilce == gelen_ilce,
        models.Kota.urun_id == gelen_urun_id
    ).first()

    # Eğer veritabanında o ilçeye ait öyle bir kayıt yoksa hata döndür
    if not kota_sorgusu:
        raise HTTPException(status_code=404, detail="Seçtiğiniz ilçe ve ürün için kota bilgisi bulunamadı.")

    # Kayıt varsa, arayüze (frontend'e) sadece istediğimiz verileri paketleyip gönderiyoruz
    return {
        "ilce": kota_sorgusu.ilce,
        "urun_id": kota_sorgusu.urun_id,
        "kullanilan_kota": kota_sorgusu.kullanilan_kota,
        "maksimum_kota": kota_sorgusu.maksimum_kota
    }"""