import { useEffect, useState } from "react";
import "../App.css";
import { URUNLER, URUN_GORUNEN_ADLAR } from "../constants/urunler";

const ILCELER = ["Bayındır","Bergama","Menderes","Tire","Torbalı","Ödemiş"];
const SEZONLAR = ["İlkbahar", "Yaz", "Sonbahar", "Kış"];

function RiskAnalysis() {
  const [kullanici, setKullanici] = useState(null);
  const [form, setForm] = useState({ ilce: "", urun: "", donum: "", sezon: "" });
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");

  useEffect(() => {
    const kayit = localStorage.getItem("kullanici");
    if (kayit) setKullanici(JSON.parse(kayit));
  }, []);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const analiziBaslat = async () => {
    setHata("");
    if (!form.ilce || !form.urun || !form.donum || !form.sezon) {
      setHata("Lütfen ilçe, ürün, dönüm ve sezon bilgisini doldur.");
      return;
    }
    if (!kullanici) {
      setHata("Önce giriş yapmalısın.");
      return;
    }

    setYukleniyor(true);
    setSonuc(null);
    try {
      const res = await fetch("http://localhost:8000/tahmin/risk", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, kullanici_id: kullanici.id }),
      });
      const data = await res.json();
      if (res.ok) {
        setSonuc(data);
      } else {
        const mesaj = typeof data.detail === "string" ? data.detail : "Tahmin alınamadı.";
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
                <option key={i} value={i}>{i}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Ürün</label>
            <select name="urun" value={form.urun} onChange={handleChange}>
              <option value="">Ürün seç</option>
              {URUNLER.map((u) => (
                <option key={u} value={u}>{URUN_GORUNEN_ADLAR[u]}</option>
              ))}
            </select>
          </div>

          <div className="field">
            <label>Dönüm</label>
            <input
              type="number"
              min="0"
              step="any"
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
                <option key={s} value={s}>{s}</option>
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
                <div className="label">{sonuc.risk_emoji} {sonuc.risk_seviyesi}</div>
                <div className="value">%{sonuc.genel_risk}</div>
                <div className="risk-gauge">
                  <div
                    className="risk-gauge-fill"
                    style={{ width: `${Math.min(sonuc.genel_risk, 100)}%` }}
                  />
                </div>
              </div>

              <div className="panel" style={{ marginTop: 16 }}>
                <h4 style={{ marginBottom: 12 }}>Risk Bileşenleri</h4>

                <div className="meta">Kota Doluluk: <strong>%{sonuc.kota_doluluk}</strong> (ağırlık: %38)</div>
                <div className="meta">Fiyat Oynaklığı (CV): <strong>%{sonuc.cv}</strong> (ağırlık: %29)</div>

                <hr style={{ margin: "12px 0", opacity: 0.2 }} />

                <div className="meta">Gübre — Güncel Fiyat: <strong>{sonuc.gubre_guncel} TL</strong></div>
                <div className="meta">Gübre Risk Katkısı: <strong>%{sonuc.gubre_riski}</strong> (ağırlık: %16)</div>

                <hr style={{ margin: "12px 0", opacity: 0.2 }} />

                <div className="meta">Mazot — Tahmini Fiyat: <strong>{sonuc.mazot_tahmini} TL</strong></div>
                <div className="meta">Mazot Risk Katkısı: <strong>%{sonuc.mazot_riski}</strong> (ağırlık: %9)</div>

                <hr style={{ margin: "12px 0", opacity: 0.2 }} />

                <div className="meta">Enflasyon — Tahmini: <strong>%{sonuc.enflasyon_tahmini}</strong></div>
                <div className="meta">Enflasyon Risk Katkısı: <strong>%{sonuc.enflasyon_riski}</strong> (ağırlık: %8)</div>
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