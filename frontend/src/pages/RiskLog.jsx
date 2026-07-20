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
              <h4>{k.sorgulanan_urun} — {k.sorgulanan_ilce}</h4>
              <div className="meta">Sezon: {k.sezon} &nbsp;|&nbsp; Dönüm: {k.girilen_donum}</div>
              <div className="meta">{new Date(k.sorgu_tarihi).toLocaleString("tr-TR")}</div>
              <div className="meta" style={{ marginTop: 8 }}>
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