from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, session
from passlib.context import CryptContext

from app import models
from app import schemas
from app.database import SessionLocal

from app.services.risk import (FIYAT_HARITASI, REFERANS, kota_doluluk_hesapla, cv_hesapla, sapma_riski_hesapla,
                               genel_risk_hesapla, risk_seviyesi_belirle, mazot_tahmini_al, enflasyon_tahmini_al,
                               guncel_gubre_fiyati_getir, SEZON_CEVIRI, )
from app.services.risk import sezon_cevir,hedef_yil_belirle,risk_hesapla
from app.services.profit_service import kar_hesaplama_son
from app.services.price_prediction import predict_product_price
from app.services.optimization_plan import create_plan_for_user_fields
from app.services.hal_price_service import fetch_daily_hal_prices

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
        bos_donum=0
        for u in urun_kayitlari:
            urun_bilgisi = db.query(models.Urun).filter(models.Urun.urun_id == u.urun_id).first()
            urunler.append({
                "urun_adi": urun_bilgisi.urun_adi,
                "donum": u.donum
            })
            #boş ürünlerin dönümü için
            if urun_bilgisi.urun_adi=="Boş":
                bos_donum+=u.donum

        sonuc.append({
            "tarla_id": t.tarla_id,
            "tarla_adi": t.tarla_adi,
            "ilce_adi": ilce.ilce_adi,
            "bos_donum": bos_donum,
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

#risk analiz
@router.post("/tahmin/risk")
def tahmin_risk(veri: schemas.RiskTahminRequest,db: Session = Depends(get_db)):
    try:
        return risk_hesapla(
            db=db,
            ilce=veri.ilce,
            urun=veri.urun,
            sezon=veri.sezon,
            donum=veri.donum,
            kullanici_id=veri.kullanici_id,
        )

    except ValueError as e:
        raise HTTPException(status_code=404,detail=str(e),)

#risk analiz logu profildeki
@router.get("/risk/gecmis", response_model=list[schemas.RiskLogResponse])
def risk_gecmisi(kullanici_id: int, db: Session = Depends(get_db)):
    kayitlar = (
        db.query(models.RiskAnalizLog)
        .filter(models.RiskAnalizLog.kullanici_id == kullanici_id)
        .order_by(models.RiskAnalizLog.sorgu_tarihi.desc())
        .all()
    )
    sonuc = []
    for k in kayitlar:
        ilce = db.query(models.Ilce).filter(models.Ilce.ilce_id == k.ilce_id).first()
        urun = db.query(models.Urun).filter(models.Urun.urun_id == k.urun_id).first()

        sonuc.append({
            "log_id": k.log_id,
            "ilce_adi": ilce.ilce_adi if ilce else None,
            "urun_adi": urun.urun_adi if urun else None,
            "sezon": k.sezon,
            "girilen_donum": k.girilen_donum,
            "kota_doluluk": k.kota_doluluk,
            "cv_fiyat": k.cv_fiyat,
            "mazot_tahmini": k.mazot_tahmini,
            "mazot_riski": k.mazot_riski,
            "enflasyon_tahmini": k.enflasyon_tahmini,
            "enflasyon_riski": k.enflasyon_riski,
            "gubre_guncel": k.gubre_guncel,
            "gubre_riski": k.gubre_riski,
            "genel_risk": k.genel_risk,
            "risk_seviyesi": k.risk_seviyesi,
            "sorgu_tarihi": k.sorgu_tarihi,
        })
    return sonuc

@router.post("/kar/hesapla")
def kar_hesapla(veri: schemas.KarHesabiRequest, db: Session = Depends(get_db)):
    ilce_kaydi = db.query(models.Ilce).filter(models.Ilce.ilce_adi == veri.ilce).first()
    urun_kaydi = db.query(models.Urun).filter(models.Urun.urun_adi == veri.urun).first()

    if not ilce_kaydi or not urun_kaydi:
        raise HTTPException(status_code=404, detail="İlçe veya ürün bulunamadı.")

    hedef_yil = hedef_yil_belirle(veri.sezon)
    hedef_sezon = sezon_cevir(veri.sezon)

    try:
        return kar_hesaplama_son(
            db=db,
            ilce=veri.ilce,
            urun=veri.urun,
            sezon=veri.sezon,
            donum=veri.donum,
            sulama_maliyeti=veri.sulama_maliyeti,
            iscilik_maliyeti=veri.iscilik_maliyeti,
            tohum_maliyeti=veri.tohum_maliyeti,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

#fiyat tahmini
@router.post("/tahmin/fiyat")
def tahmin_fiyat(veri: schemas.FiyatTahminRequest,db: Session=Depends(get_db)):
    urun_kaydi = db.query(models.Urun).filter(models.Urun.urun_adi == veri.urun).first()
    if not urun_kaydi:
        raise HTTPException(status_code=404,detail="Urun bulanamdi..")

    hedef_sezon = sezon_cevir(veri.sezon)

    sonuc = predict_product_price(product_name=veri.urun,target_season=hedef_sezon)

    return {
        "sezon":veri.sezon,
        "urun":veri.urun,
        "tahmini_fiyat": sonuc["predicted_price"]
    }
    
#urunler
@router.get("/urunlerim/{kullanici_id}")
def kullanici_urunleri(kullanici_id:int,db:Session=Depends(get_db)):
    #kullanıcıya ait tarlarar getirir,
    tarlalar= (db.query(models.Tarla).filter(models.Tarla.kullanici_id == kullanici_id).all())
    if not tarlalar:
        return []

    urun_map={}
    for tarla in tarlalar:
        tarla_urunleri=db.query(models.TarlaUrun).filter(models.TarlaUrun.tarla_id == tarla.tarla_id).all()

        for tarla_urun in tarla_urunleri:
            urun=db.query(models.Urun).filter(models.Urun.urun_id == tarla_urun.urun_id).first()
            if not urun:
                continue

        #daha önce eklenmemisse oluştur
            if urun.urun_adi not in urun_map:
                urun_map[urun.urun_adi]={
                "urun_adi":urun.urun_adi,
                "toplam_donum": 0,
                "tarlalar" : []
            }

            #toplam alan hesaplama
            urun_map[urun.urun_adi]["toplam_donum"] += tarla_urun.donum

            #hangi tarlalarda var bilgisini ekleme
            urun_map[urun.urun_adi]["tarlalar"].append({
                "tarla_adi":  tarla.tarla_adi,
                "donum":tarla_urun.donum
            })

    sonuc=list(urun_map.values())
    sonuc.sort(key=lambda x: x["toplam_donum"],reverse=True)

    return sonuc

@router.post("/oneri/tarla_getir")
def optimize_ekim_planı(veri:schemas.OptimizationTarlaRequest,db: Session=Depends(get_db)):
    kullanici = (db.query(models.Kullanici).filter(models.Kullanici.kullanici_id == veri.kullanici_id).first())
    if not kullanici:
        raise HTTPException(
            status_code=404,
            detail="Kullanıcı bulunamadı."
        )

    tarla = (db.query(models.Tarla).filter(models.Tarla.tarla_id==veri.tarla_id,models.Tarla.kullanici_id==veri.kullanici_id).first())
    if not tarla:
        raise HTTPException(status_code=404,detail="Tarla bulunamadı")

    ilce = (db.query(models.Ilce).filter(models.Ilce.ilce_id == tarla.ilce_id).first())

    fields=[{
        "id":tarla.tarla_id,
        "district":ilce.ilce_adi,
        "area": veri.bos_donum
    }]
    SEZON_CEVIR={
        "İlkbahar":"Spring",
        "Sonbahar":"Fall",
        "Kış":"Winter",
        "Yaz":"Summer"
    }
    season = SEZON_CEVIR[veri.sezon]

    plan =create_plan_for_user_fields(
        db=db,
        fields=fields,
        season=season,
        selected_products=veri.secilen_urunler
    )

    return plan

@router.post("/oneri/manual")
def manuel_optimized(veri:schemas.OptimizationManuelRequest,db: Session=Depends(get_db)):
    fields=[{
        "id":0, #tarlalar içinde seçim yapmayacagı için
        "district":veri.ilce_adi,
        "area":veri.donum
    }]
    SEZON_CEVIR={
        "İlkbahar":"Spring",
        "Sonbahar":"Fall",
        "Yaz":"Summer",
        "Kış":"Winter"
    }
    season = SEZON_CEVIR[veri.sezon]

    plan = create_plan_for_user_fields(
        db=db,
        fields=fields,
        season=season,
        selected_products=veri.secilen_urunler
    )
    return plan

@router.get("/istatistikler/hal-fiyatlari")
def get_daily_hal_prices():
    try:
        data = fetch_daily_hal_prices()

        return data
       
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Hal fiyatları alınamadı: {str(error)}",
        )
