import enum
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.sql import func
from app.database import Base

# Ekim kaydındaki durum alanı için Python Enum yapısı
class DurumEnum(str, enum.Enum):
    aktif = "aktif"
    hasat_edildi = "hasat_edildi"
    iptal = "iptal"

# kullanıcı modeli
class Kullanici(Base):
    __tablename__="kullanici"

    kullanici_id=Column(Integer,primary_key=True,index=True,autoincrement=True)
    ad_soyad=Column(String(100),nullable=False)
    email=Column(String(100),unique=True,nullable=False)
    sifre_hash=Column(String(255),nullable=False)
    yas=Column(Integer,nullable=True)
    cinsiyet=Column(String(20),nullable=True)
    telefon=Column(String(20),nullable=True)
    kayit_tarihi=Column(DateTime,server_default=func.now())

#ürün modeli
class Urun(Base):
    __tablename__ = "urun"

    urun_id = Column(Integer, primary_key=True, autoincrement=True)
    urun_adi = Column(String(50), nullable=False)

#ilce modeli
class Ilce(Base):
    __tablename__ = "ilce"

    ilce_id = Column(Integer, primary_key=True, autoincrement=True)
    ilce_adi = Column(String(50), unique=True, nullable=False)

# tarla modeli
class Tarla(Base):
    __tablename__ = "tarla"

    tarla_id = Column(Integer, primary_key=True, autoincrement=True)
    kullanici_id = Column(Integer, ForeignKey("kullanici.kullanici_id", ondelete="CASCADE"), nullable=False)
    tarla_adi = Column(String(100))
    ilce_id = Column(Integer,ForeignKey("ilce.ilce_id"), nullable=False)

class TarlaUrun(Base):
    __tablename__="tarla_urun"

    tarla_urun_id=Column(Integer,primary_key=True,autoincrement=True)
    tarla_id=Column(
        Integer,
        ForeignKey("tarla.tarla_id",ondelete="CASCADE")
    )
    urun_id=Column(
        Integer,
        ForeignKey("urun.urun_id",ondelete="CASCADE")
    )
    donum=Column(Float,nullable=False)

# kota modeli
class Kota(Base):
    __tablename__ = "kota"

    kota_id = Column(Integer, primary_key=True, autoincrement=True)
    urun_id = Column(Integer, ForeignKey("urun.urun_id", ondelete="CASCADE"), nullable=False)
    ilce_id = Column(Integer, ForeignKey("ilce.ilce_id"),nullable=False)
    maksimum_kota = Column(Float,ForeignKey("ilce.ilce_id"), nullable=False)
    kullanilan_kota = Column(Float, default=0)

# öneri paketi modeli
class OneriPaketi(Base):
    __tablename__ = "oneri_paketi"

    paket_id = Column(Integer, primary_key=True, autoincrement=True)
    kullanici_id = Column(Integer, ForeignKey("kullanici.kullanici_id", ondelete="CASCADE"), nullable=False)
    tarla_id = Column(Integer, ForeignKey("tarla.tarla_id", ondelete="CASCADE"), nullable=False)
    hesaplanan_toplam_kar = Column(Float, nullable=True) # Backend'de biz hesaplayacağız
    basit_skor = Column(Integer, nullable=True)          # Algoritmanın üreteceği o sade puan
    kabul_edildi_mi = Column(Boolean, default=False)
    olusturma_tarihi = Column(DateTime, server_default=func.now())

# ekim kaydı
class EkimKaydi(Base):
    __tablename__ = "ekim_kaydi"

    kayit_id = Column(Integer, primary_key=True, autoincrement=True)
    paket_id = Column(Integer, ForeignKey("oneri_paketi.paket_id", ondelete="CASCADE"), nullable=False)
    urun_id = Column(Integer, ForeignKey("urun.urun_id", ondelete="CASCADE"), nullable=False)
    ekilen_donum = Column(Float, nullable=False)
    durum = Column(Enum(DurumEnum), default=DurumEnum.aktif, nullable=False)

# risk analiz log modeli
class RiskAnalizLog(Base):
    __tablename__ = "risk_analiz_log"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    kullanici_id = Column(Integer, ForeignKey("kullanici.kullanici_id", ondelete="SET NULL"), nullable=True)
    sorgulanan_ilce = Column(String(50), nullable=False)
    urun_id = Column(Integer, ForeignKey("urun.urun_id", ondelete="CASCADE"), nullable=False)
    girilen_donum = Column(Float, nullable=False)
    donen_risk_orani = Column(Float, nullable=True)
    sorgu_tarihi = Column(DateTime, server_default=func.now())

# kullanıcı aktivite log modeli
class KullaniciAktiviteLog(Base):
    __tablename__ = "kullanici_aktivite_log"

    aktivite_id = Column(Integer, primary_key=True, autoincrement=True)
    kullanici_id = Column(Integer, ForeignKey("kullanici.kullanici_id", ondelete="CASCADE"), nullable=False)
    islem_tipi = Column(String(100), nullable=False)
    ip_adresi = Column(String(45), nullable=True)
    islem_tarihi = Column(DateTime, server_default=func.now())