from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime

# Kullanıcı şemalrı ( kayıt ve giriş yapmak için)

class KullaniciBase(BaseModel):

    ad_soyad:str
    email:EmailStr
    yas:int | None = None
    cinsiyet:str | None = None
    telefon:str | None = None


class KullaniciCreate(KullaniciBase):

    sifre:str


class KullaniciLogin(BaseModel):

    email:EmailStr
    sifre:str


class KullaniciUpdate(BaseModel):

    kullanici_id:int
    ad_soyad:str
    yas:int | None=None
    cinsiyet:str | None=None
    telefon:str | None=None


class KullaniciResponse(KullaniciBase):

    kullanici_id:int
    kayit_tarihi:datetime
    model_config = ConfigDict(from_attributes=True)


class TarlaUrunCreate(BaseModel):
    urun_id: int
    donum: float


class TarlaCreate(BaseModel):
    kullanici_id: int
    tarla_adi: str
    ilce_id: int

    urunler: list[TarlaUrunCreate] #kullanıcı aynı tarlaya birden fazla ürün ekebilir o yüzden bunları liste olarak tutmak laızm

class RiskTahminRequest(BaseModel):
    ilce: str
    urun: str
    donum: float = Field(..., gt=0)
    sezon: str | None = None
    kullanici_id:int

class RiskLogResponse(BaseModel):
    log_id: int
    sorgulanan_ilce: str
    sorgulanan_urun: str
    sezon: str
    girilen_donum: float
    kota_doluluk: float | None
    cv_fiyat: float | None
    mazot_tahmini: float | None
    mazot_riski: float | None
    enflasyon_tahmini: float | None
    enflasyon_riski: float | None
    gubre_guncel: float | None
    gubre_riski: float | None
    genel_risk: float | None
    risk_seviyesi: str | None
    sorgu_tarihi: datetime

    model_config = ConfigDict(from_attributes=True)