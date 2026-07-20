from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from passlib.context import CryptContext

import models
from app import schemas
from app.database import SessionLocal

from app.services.risk import FIYAT_HARITASI, kota_doluluk_hesapla, cv_hesapla, genel_risk_hesapla, risk_seviyesi_belirle

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
@router.post("/kullanici/kayit", response_model=schemas.KullaniciResponse)
def kullanici_kayit(kullanici: schemas.KullaniciCreate, db:Session=Depends(get_db)):
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
def giris(kullanici: schemas.KullaniciLogin, db:Session=Depends(get_db)):
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
def kullanici_guncelle(veri: schemas.KullaniciUpdate, db:Session=Depends(get_db)):
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

#ilçe listesi select için
@router.get("/ilce/liste")
def ilce_liste(db: Session = Depends(get_db)):
    return db.query(models.Ilce).all()

#formdaki select için ürün list
@router.get("/urun/liste")
def urun_liste(db: Session = Depends(get_db)):
    return db.query(models.Urun).all()

#tarla ekleme
@router.post("/tarla/ekle")
def tarla_ekle(veri: schemas.TarlaCreate, db: Session = Depends(get_db)):
    yeni_tarla = models.Tarla(
        kullanici_id=veri.kullanici_id,
        tarla_adi=veri.tarla_adi,
        ilce_id=veri.ilce_id
    )
    db.add(yeni_tarla)
    db.commit()
    db.refresh(yeni_tarla)

    for satir in veri.urunler:
        db.add(models.TarlaUrun(
            tarla_id=yeni_tarla.tarla_id,
            urun_id=satir.urun_id,
            donum=satir.donum
        ))

        # O ilçe ürün için kota kaydı varsa, kullanılan kotayı arttır
        kota_kaydi = db.query(models.Kota).filter(
            models.Kota.ilce_id == veri.ilce_id,
            models.Kota.urun_id == satir.urun_id
        ).first()

        if kota_kaydi:
            kota_kaydi.kullanilan_kota = (kota_kaydi.kullanilan_kota or 0) + satir.donum
    db.commit()
    return {"mesaj": "Tarla başarıyla eklendi."}

#tarla listeleme
@router.get("/tarla/liste")
def tarla_liste(kullanici_id: int, db: Session = Depends(get_db)):
    tarlalar = db.query(models.Tarla).filter(models.Tarla.kullanici_id == kullanici_id).all()

    sonuc = []
    for t in tarlalar:
        ilce = db.query(models.Ilce).filter(models.Ilce.ilce_id == t.ilce_id).first()
        urun_kayitlari = db.query(models.TarlaUrun).filter(models.TarlaUrun.tarla_id == t.tarla_id).all()

        urunler = []
        for u in urun_kayitlari:
            urun_bilgisi = db.query(models.Urun).filter(models.Urun.urun_id == u.urun_id).first()
            urunler.append({
                "urun_adi": urun_bilgisi.urun_adi,
                "donum": u.donum
            })

        sonuc.append({
            "tarla_id": t.tarla_id,
            "tarla_adi": t.tarla_adi,
            "ilce_adi": ilce.ilce_adi,
            "urunler": urunler
        })
    return sonuc

#tarla silme
@router.delete("/tarla/sil/{tarla_id}")
def tarla_sil(tarla_id: int, db: Session = Depends(get_db)):
    tarla = db.query(models.Tarla).filter(models.Tarla.tarla_id == tarla_id).first()
    if not tarla:
        raise HTTPException(status_code=404, detail="Tarla bulunamadı.")

    # Bu tarlaya bağlı ürün kayıtlarını al
    urun_kayitlari = db.query(models.TarlaUrun).filter(models.TarlaUrun.tarla_id == tarla_id).all()

    # Silmeden önce, her ürün için kullanılan kotayı geri düş
    for u in urun_kayitlari:
        kota_kaydi = db.query(models.Kota).filter(
            models.Kota.ilce_id == tarla.ilce_id,
            models.Kota.urun_id == u.urun_id
        ).first()
        if kota_kaydi:
            kota_kaydi.kullanilan_kota = max(0, (kota_kaydi.kullanilan_kota or 0) - u.donum)

    # Sonra ürün kayıtlarını ve tarlayı sil
    db.query(models.TarlaUrun).filter(models.TarlaUrun.tarla_id == tarla_id).delete()
    db.delete(tarla)
    db.commit()

    return {"mesaj": "Tarla silindi."}

#risk tahmini
@router.post("/tahmin/risk")
def tahmin_risk(veri: schemas.RiskTahminRequest, db: Session = Depends(get_db)):

    ilce_kaydi = db.query(models.Ilce).filter(models.Ilce.ilce_adi == veri.ilce).first()
    urun_kaydi = db.query(models.Urun).filter(models.Urun.urun_adi == veri.urun).first()

    if not ilce_kaydi or not urun_kaydi:
        raise HTTPException(status_code=404, detail="İlçe veya ürün bulunamadı.")

    kota_kaydi = db.query(models.Kota).filter(
        models.Kota.ilce_id == ilce_kaydi.ilce_id,
        models.Kota.urun_id == urun_kaydi.urun_id
    ).first()

    if not kota_kaydi:
        raise HTTPException(status_code=404, detail="Bu ilçe ve ürün için kota kaydı bulunamadı.")

    kota_doluluk = kota_doluluk_hesapla(
        kullanilan_kota=kota_kaydi.kullanilan_kota or 0,
        girilen_donum=veri.donum,
        maksimum_kota=kota_kaydi.maksimum_kota
    )

    fiyatlar = FIYAT_HARITASI.get(veri.urun)
    if not fiyatlar or len(fiyatlar) < 2:
        raise HTTPException(status_code=404, detail="Bu ürün için fiyat geçmişi bulunamadı.")

    cv, ortalama, std = cv_hesapla(fiyatlar)
    genel_risk = genel_risk_hesapla(kota_doluluk, cv)
    seviye, emoji = risk_seviyesi_belirle(genel_risk)

    return {
        "kota_doluluk": round(kota_doluluk, 2),
        "cv": round(cv, 2),
        "genel_risk": round(genel_risk, 2),
        "risk_seviyesi": seviye,
        "risk_emoji": emoji
    }