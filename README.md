#  Tarımsal Karar Destek Sistemi

Tarımsal Karar Destek Sistemi; geçmiş tarımsal veriler, makine öğrenmesi ve matematiksel optimizasyon yöntemlerini kullanarak üreticilere **veriye dayalı ekim planı ve risk analizi** sunmayı amaçlayan bir karar destek uygulamasıdır.

Kullanıcı il, ilçe ve arazi büyüklüğünü girerek bölgesine uygun ürünleri inceleyebilir ve arazisinin ürünler arasında nasıl paylaştırılabileceğine dair öneriler alabilir.

## 🚀 Temel Özellikler

- 📍 İl ve ilçe bazlı uygun ürünlerin belirlenmesi
- 📊 Geçmiş üretim ve ekim alanı verilerinin analizi
- 🤖 Makine öğrenmesi ile ürün fiyat tahmini
- 🌾 Dönüm başına ortalama verim hesaplama
- 💰 Tahmini üretim, gelir ve kârlılık analizi
- ⚠️ Tarlada kalma / arz fazlası risk analizi
- 📏 Güvenli ekim kotasının değerlendirilmesi
- 🧮 PuLP ile optimal ekim alanı dağılımı

## 🧠 Sistem Nasıl Çalışır?

Kullanıcıdan alınan:

`İl + İlçe + Arazi Büyüklüğü`

bilgileri doğrultusunda bölgeye uygun ürünler belirlenir.

Ardından geçmiş üretim, fiyat ve maliyet verileri kullanılarak ürünlerin verim ve ekonomik potansiyelleri analiz edilir. Makine öğrenmesi modeli gelecek dönem ürün fiyatlarının tahmininde kullanılır.

Risk ve kota bilgileri de değerlendirilerek PuLP tabanlı optimizasyon modeli toplam araziyi uygun ürünler arasında paylaştırır.

```text
Kullanıcı Bilgileri
        ↓
Bölgeye Uygun Ürünler
        ↓
Veri Analizi & Feature Engineering
        ↓
Fiyat Tahmini
        ↓
Gelir / Kârlılık Analizi
        ↓
Risk & Kota Analizi
        ↓
PuLP Optimizasyonu
        ↓
Optimal Ekim Planı
```

## 🛠️ Kullanılan Teknolojiler

- Python
- Pandas
- Scikit-learn
- Machine Learning
- Random Forest
- PuLP
- FastAPI
- React.js
- SQL
- Git / GitHub

## 📊 Kullanılan Veri Türleri

Sistemde başlıca;

- ürün fiyatları,
- ekim alanı,
- üretim miktarı,
- mazot fiyatları,
- gübre fiyatları,
- enflasyon,
- yıl ve sezon

gibi veriler kullanılmaktadır.

Bu veriler temizleme, birleştirme ve feature engineering işlemlerinden geçirilerek makine öğrenmesi ve optimizasyon modellerine uygun hale getirilmektedir.

## 🎯 Projenin Amacı

Projenin amacı yalnızca en yüksek gelir potansiyeline sahip ürünü önermek değil; **kârlılık, üretim kapasitesi, arz riski ve ekim sınırlarını birlikte değerlendirerek daha dengeli bir üretim planı oluşturmaktır.**

Böylece üreticilerin veriye dayalı karar vermelerine ve mevcut tarım alanlarını daha verimli planlamalarına destek olunması hedeflenmektedir.
