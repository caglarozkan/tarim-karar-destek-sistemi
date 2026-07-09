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

# ==========================================
# 1. KULLANICI KAYIT (Ad, Soyad, Email, Şifre Alıp DB'ye Ekler)
# ==========================================
@router.post("/kullanici/kayit", response_model=schemas.KullaniciResponse, status_code=status.HTTP_201_CREATED)
def kullanici_kayit(kullanici: schemas.KullaniciCreate, db: Session = Depends(get_db)):
    # Aynı email var mı kontrolü
    db_kullanici = db.query(models.Kullanici).filter(models.Kullanici.email == kullanici.email).first()
    if db_kullanici:
        raise HTTPException(status_code=400, detail="Bu email sistemde zaten kayıtlı!")

    # Şifreyi hash'le ve yeni kullanıcıyı oluştur
    yeni_kullanici = models.Kullanici(
        ad_soyad=kullanici.ad_soyad,
        email=kullanici.email,
        sifre_hash=get_password_hash(kullanici.sifre)
    )
    db.add(yeni_kullanici)
    #db.commit()
    #db.refresh(yeni_kullanici)  # MySQL'in otomatik verdiği kullanici_id'yi çeker
    return yeni_kullanici


# ==========================================
# 2. GİRİŞ YAP VE AKTİVİTE LOGU TUT
# ==========================================
@router.post("/kullanici/giris")
def kullanici_giris(kullanici: schemas.KullaniciLogin, db: Session = Depends(get_db)):
    db_kullanici = db.query(models.Kullanici).filter(models.Kullanici.email == kullanici.email).first()
    if not db_kullanici or not verify_password(kullanici.sifre, db_kullanici.sifre_hash):
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı!")

    # GİRİŞ BAŞARILI: Hemen kullanici_aktivite_log tablosuna yazıyoruz
    yeni_log = models.KullaniciAktiviteLog(
        kullanici_id=db_kullanici.kullanici_id,
        islem_tipi="Sisteme Başarılı Giriş Yapıldı"
    )
    db.add(yeni_log)
    #db.commit()

    return {
        "mesaj": "Giriş başarılı, hoş geldin!",
        "kullanici_id": db_kullanici.kullanici_id,
        "ad_soyad": db_kullanici.ad_soyad
    }


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


# ==========================================
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
    #db.commit()
    return {"mesaj": "Risk analizi verileri başarıyla loglandı."}