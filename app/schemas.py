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