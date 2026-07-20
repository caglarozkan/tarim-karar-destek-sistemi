from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional
from datetime import datetime


class KullaniciBase(BaseModel):
    ad_soyad: str
    email: EmailStr


class KullaniciCreate(KullaniciBase):
    sifre: str


class KullaniciLogin(BaseModel):
    email: EmailStr
    sifre: str


class KullaniciResponse(KullaniciBase):
    kullanici_id: int
    kayit_tarihi: datetime

    model_config = ConfigDict(from_attributes=True)

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

# ==========================================
# RİSK ANALİZİ ŞEMASI (Hesaplama Logu İçin)
# ==========================================
class RiskAnalizRequest(BaseModel):
    sorgulanan_ilce: str
    urun_id: int
    girilen_donum: float = Field(..., gt=0)