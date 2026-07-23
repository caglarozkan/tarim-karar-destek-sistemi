import { useEffect, useState } from "react";
import "../App.css";

function RiskLog() {
  const [kayitlar, setKayitlar] = useState([]);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");

  useEffect(() => {
    const kayit = localStorage.getItem("kullanici");
    if (!kayit) return;
    const user = JSON.parse(kayit);

    fetch(`http://localhost:8000/risk/gecmis?kullanici_id=${user.id}`)
      .then((res) => res.json())
      .then((data) => setKayitlar(data))
      .catch(() => setHata("Geçmiş yüklenemedi."))
      .finally(() => setYukleniyor(false));
  }, []);

  return (
    <div className="page-container">
      <div className="analysis-header">
        <span className="eyebrow">Profilim</span>
        <h2>Risk Analiz Geçmişi</h2>
      </div>

      {hata && <div className="form-message error">{hata}</div>}

      {yukleniyor ? (
        <div className="empty-state">Yükleniyor...</div>
      ) : kayitlar.length === 0 ? (
        <div className="panel"><div className="empty-state">Henüz bir risk analizi yapmadın.</div></div>
      ) : (
        <div className="farms-list">
          {kayitlar.map((k) => (
            <div className="farm-card" key={k.log_id}>
              <h4>{k.urun_adi} — {k.ilce_adi}</h4>
              <div className="meta">{new Date(k.sorgu_tarihi).toLocaleString("tr-TR")}</div>

              <div style={{ marginTop: 10, marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
                Girilen Bilgiler
              </div>
              <div className="meta">Sezon: {k.sezon}</div>
              <div className="meta">Dönüm: {k.girilen_donum}</div>

              <div style={{ marginTop: 10, marginBottom: 6, fontWeight: 600, fontSize: 13 }}>
                Hesaplanan Değerler
              </div>
              <div className="meta">Kota Doluluk: %{k.kota_doluluk}</div>
              <div className="meta">Fiyat Oynaklığı (CV): %{k.cv_fiyat}</div>
              <div className="meta">Gübre — Güncel Fiyat: {k.gubre_guncel} TL, Risk: %{k.gubre_riski}</div>
              <div className="meta">Mazot — Tahmini Fiyat: {k.mazot_tahmini} TL, Risk: %{k.mazot_riski}</div>
              <div className="meta">Enflasyon — Tahmini: %{k.enflasyon_tahmini}, Risk: %{k.enflasyon_riski}</div>

              <div className="meta" style={{ marginTop: 10 }}>
                <strong>{k.risk_seviyesi}</strong> — Genel Risk: %{k.genel_risk}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default RiskLog;