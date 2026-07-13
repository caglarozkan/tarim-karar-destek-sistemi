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



"""# TARLA ŞEMALARI (Tarla Ekleme İçin)
class TarlaBase(BaseModel):
    tarla_adi: Optional[str] = None
    toplam_donum: float = Field(..., gt=0, description="Dönüm sıfırdan büyük olmalı")
    ilce: str


class TarlaCreate(TarlaBase):
    pass

class TarlaResponse(TarlaBase):
    tarla_id: int
    kullanici_id: int

    model_config = ConfigDict(from_attributes=True)

# RİSK ANALİZİ ŞEMASI (Hesaplama Logu İçin)

class RiskAnalizRequest(BaseModel):
    sorgulanan_ilce: str
    urun_id: int
    girilen_donum: float = Field(..., gt=0)"""