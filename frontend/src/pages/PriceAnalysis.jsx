import { useState } from "react";
import "../App.css";
import { URUN_GORUNEN_ADLAR } from "../constants/urunler";
import { PRODUCT_IMAGES } from "../constants/productImages";
import ProductSelect from "../components/ProductSelect";

const SEZONLAR = ["İlkbahar", "Yaz", "Sonbahar", "Kış"];

function PriceAnalysis() {
  const [form, setForm] = useState({ sezon: "", urun: "" });
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const analiziBaslat = async () => {
    setHata("");

    if (!form.sezon || !form.urun) {
      setHata("Lütfen sezon ve ürün seçimini tamamla.");
      return;
    }

    setYukleniyor(true);
    setSonuc(null);

    try {
      const res = await fetch("http://localhost:8000/tahmin/fiyat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });

      const data = await res.json();

      if (res.ok) {
        setSonuc(data);
      } else {
        const mesaj =
          typeof data.detail === "string" ? data.detail : "Tahmin alınamadı.";
        setHata(mesaj);
      }
    } catch {
      setHata("Sunucuya bağlanılamadı.");
    } finally {
      setYukleniyor(false);
    }
  };

  return (
    <div className="page-container">
      <div className="analysis-header">
        <span className="eyebrow">Fiyat Tahmini</span>
        <h2>Ürün Fiyat Analizi</h2>
      </div>

      <div className="analysis-grid">
        <div className="panel">
          <h3>Seçim Kriterleri</h3>

          <div className="field">
            <label>Sezon Seçimi</label>
            <select name="sezon" value={form.sezon} onChange={handleChange}>
              <option value="">Sezon seç</option>
              {SEZONLAR.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Ürün Seçimi</label>
            <ProductSelect
              value={form.urun}
              onChange={(urun) =>
                setForm((prev) => ({
                  ...prev,
                  urun,
                }))
              }
            />
          </div>

          {hata && <div className="form-message error">{hata}</div>}

          <button
            className="run-btn"
            onClick={analiziBaslat}
            disabled={yukleniyor}
          >
            {yukleniyor ? "Hesaplanıyor..." : "Analizi Başlat"}
          </button>
        </div>

        <div className="results-column">
          {sonuc ? (
            <div className="result-card hero-result">
              {PRODUCT_IMAGES[sonuc.urun] && (
                <img
                  src={PRODUCT_IMAGES[sonuc.urun]}
                  className="product-result-image"
                  alt={sonuc.urun}
                />
              )}

              <div className="label">Tahmini Fiyat</div>
              <div className="value">{sonuc.tahmini_fiyat} ₺</div>

              <div className="meta" style={{ marginTop: 10, color: "#f5f0e6" }}>
                {URUN_GORUNEN_ADLAR[sonuc.urun] || sonuc.urun}
              </div>

              <div className="meta" style={{ color: "#f5f0e6" }}>
                {sonuc.sezon} {sonuc.yil}
              </div>
            </div>
          ) : (
            <div className="panel">
              <div className="empty-state">
                Seçimlerini yap ve "Analizi Başlat" butonuna bas — tahmini
                kilogram fiyatı burada görünecek.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PriceAnalysis;