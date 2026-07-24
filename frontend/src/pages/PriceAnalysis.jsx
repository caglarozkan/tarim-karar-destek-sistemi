import { useState } from "react";
import "../App.css";
import { URUNLER, URUN_GORUNEN_ADLAR } from "../constants/urunler";

const ILCELER = ["Bayındır","Bergama","Menderes","Tire","Torbalı","Ödemiş"];
const SEZONLAR = ["İlkbahar", "Yaz", "Sonbahar", "Kış"];

function PriceAnalysis() {
  const [form, setForm] = useState({ ilce: "", sezon: "", urun: "" });
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const analiziBaslat = async () => {
    setHata("");
    if (!form.ilce || !form.sezon || !form.urun) {
      setHata("Lütfen ilçe, sezon ve ürün seçimini tamamla.");
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
        const mesaj = typeof data.detail === "string" ? data.detail : "Tahmin Alınamadı";
        setHata(mesaj);
      }
    } catch (err) {
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
            <label>İlçe Seçimi</label>
            <select name="ilce" value={form.ilce} onChange={handleChange}>
              <option value="">İlçe seç</option>
              {ILCELER.map((i) => (
                <option key={i} value={i}>
                  {i}
                </option>
              ))}
            </select>
          </div>

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
            <select name="urun" value={form.urun} onChange={handleChange}>
              <option value="">Ürün seç</option>
              {URUNLER.map((u) => (
                <option key={u} value={u}>
                  {URUN_GORUNEN_ADLAR[u]}
                </option>
              ))}
            </select>
          </div>

          {hata && <div className="form-message error">{hata}</div>}

          <button className="run-btn" onClick={analiziBaslat} disabled={yukleniyor}>
            {yukleniyor ? "Hesaplanıyor..." : "Analizi Başlat"}
          </button>
        </div>

        <div className="results-column">
          {sonuc ? (
            <div className="result-card hero-result">
              <div className="label">Tahmini Fiyat</div>
              <div className="value">{sonuc.tahmini_fiyat} ₺</div>
              <div classname="meta" style={{marginTop:10,color: "#f5f0e6"}}>
                  {URUN_GORUNEN_ADLAR[sonuc.urun] || sonuc.urun} - {sonuc.ilce}
              </div>
              <div classname="meta" style={{color: "#f5f0e6"}}>
                  {sonuc.sezon} {sonuc.yil}
              </div>
            </div>
          ) : (
            <div className="panel">
              <div className="empty-state">
                Seçimlerini yap ve "Analizi Başlat" butonuna bas — tahmini kilogram fiyatı
                burada görünecek.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PriceAnalysis;
