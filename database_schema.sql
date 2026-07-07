CREATE DATABASE tarim_kds;
USE tarim_kds;

CREATE TABLE kullanici (
    kullanici_id INT AUTO_INCREMENT PRIMARY KEY,
    ad_soyad VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    sifre_hash VARCHAR(255) NOT NULL,
    kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE urun (
    urun_id INT AUTO_INCREMENT PRIMARY KEY,
    urun_adi VARCHAR(50) NOT NULL
);

CREATE TABLE tarla (
    tarla_id INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_id INT,
    tarla_adi VARCHAR(100),
    toplam_donum FLOAT NOT NULL,
    ilce VARCHAR(50) NOT NULL,
    FOREIGN KEY (kullanici_id) REFERENCES kullanici(kullanici_id) ON DELETE CASCADE
);

CREATE TABLE kota (
    kota_id INT AUTO_INCREMENT PRIMARY KEY,
    urun_id INT,
    ilce VARCHAR(50) NOT NULL,
    maksimum_kota FLOAT NOT NULL,
    kullanilan_kota FLOAT DEFAULT 0,
    FOREIGN KEY (urun_id) REFERENCES urun(urun_id) ON DELETE CASCADE
);

CREATE TABLE oneri_paketi (
    paket_id INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_id INT,
    tarla_id INT,
    hesaplanan_toplam_kar FLOAT,  -- Senin API'nin hesaplayıp yazacağı tutar
    basit_skor INT,               -- O ufak, basit öneri puanımız
    kabul_edildi_mi BOOLEAN DEFAULT FALSE,
    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kullanici_id) REFERENCES kullanici(kullanici_id) ON DELETE CASCADE,
    FOREIGN KEY (tarla_id) REFERENCES tarla(tarla_id) ON DELETE CASCADE
);

CREATE TABLE ekim_kaydi (
    kayit_id INT AUTO_INCREMENT PRIMARY KEY,
    paket_id INT NOT NULL,
    urun_id INT NOT NULL,
    ekilen_donum FLOAT NOT NULL,
    durum ENUM('aktif', 'hasat_edildi', 'iptal') DEFAULT 'aktif',
    FOREIGN KEY (paket_id) REFERENCES oneri_paketi(paket_id) ON DELETE CASCADE,
    FOREIGN KEY (urun_id) REFERENCES urun(urun_id) ON DELETE CASCADE
);

CREATE TABLE risk_analiz_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_id INT NULL,
    sorgulanan_ilce VARCHAR(50) NOT NULL,
    urun_id INT,
    girilen_donum FLOAT NOT NULL,
    donen_risk_orani FLOAT,
    sorgu_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kullanici_id) REFERENCES kullanici(kullanici_id) ON DELETE SET NULL,
    FOREIGN KEY (urun_id) REFERENCES urun(urun_id) ON DELETE CASCADE
);

CREATE TABLE kullanici_aktivite_log (
    aktivite_id INT AUTO_INCREMENT PRIMARY KEY,
    kullanici_id INT,
    islem_tipi VARCHAR(100) NOT NULL,
    ip_adresi VARCHAR(45),
    islem_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (kullanici_id) REFERENCES kullanici(kullanici_id) ON DELETE CASCADE
);