import { useState } from "react";
import "../App.css";

const ILCELER = ["Bayındır","Bergama","Menderes","Tire","Torbalı","Ödemiş"];
const URUNLER = ["Biber (Sivri)","Domates (Sofralık)","Hıyar (Sofralık)","Kabak (Sakız)","Karpuz","Patlıcan","Soğan (Kuru)"];
const SEZONLAR = ["İlkbahar", "Yaz", "Sonbahar", "Kış"];

function RiskAnalysis() {
  const [form, setForm] = useState({ ilce: "", urun: "", donum: "", sezon: "" });
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const analiziBaslat = async () => {
    setHata("");
    if (!form.ilce || !form.urun || !form.donum || !form.sezon) {
      setHata("Lütfen ilçe, ürün, dönüm ve sezon bilgisini doldur.");
      return;
    }

    setYukleniyor(true);
    setSonuc(null);
    try {
      const res = await fetch("http://localhost:8000/tahmin/risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json();
      if (res.ok) {
        setSonuc(data);
      } else {
        setHata(data.detail || "Tahmin alınamadı.");
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
        <span className="eyebrow">Risk Analizi</span>
        <h2>Ürün Risk Değerlendirmesi</h2>
      </div>

      <div className="analysis-grid">
        <div className="panel">
          <h3>Tarla Bilgileri</h3>

          <div className="field">
            <label>İlçe</label>
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
            <label>Ürün</label>
            <select name="urun" value={form.urun} onChange={handleChange}>
              <option value="">Ürün seç</option>
              {URUNLER.map((u) => (
                <option key={u} value={u}>
                  {u}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Dönüm</label>
            <input
              type="number"
              min="0"
              step="0.1"
              name="donum"
              placeholder="Örn. 5"
              value={form.donum}
              onChange={handleChange}
            />
          </div>

          <div className="field">
            <label>Sezon</label>
            <select name="sezon" value={form.sezon} onChange={handleChange}>
              <option value="">Sezon seç</option>
              {SEZONLAR.map((s) => (
                <option key={s} value={s}>
                  {s}
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
            <>
              <div className="result-card">
                <div className="label">Risk Oranı</div>
                <div className="value">%{sonuc.risk_orani}</div>
                <div className="risk-gauge">
                  <div
                    className="risk-gauge-fill"
                    style={{ width: `${Math.min(sonuc.risk_orani, 100)}%` }}
                  />
                </div>
              </div>
              <div className="result-note">
                {sonuc.aciklama ||
                  `Bölgedeki kalan doluluk oranının %${sonuc.doluluk_orani ?? "-"} olması bu skoru etkiliyor.`}
              </div>
            </>
          ) : (
            <div className="panel">
              <div className="empty-state">
                Tarla bilgilerini doldur — tarlada kalma ve fiyat dalgalanma riski burada
                görünecek.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default RiskAnalysis;
