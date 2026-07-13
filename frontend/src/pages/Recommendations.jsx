import { useEffect, useState } from "react";
import "../App.css";

const ILCELER = ["Bayındır", "Ödemiş", "Tire", "Kiraz", "Bergama"];

function Recommendations() {
  const kayit = localStorage.getItem("kullanici");
  const aktifKullanici = kayit ? JSON.parse(kayit) : null;

  const [mod, setMod] = useState(aktifKullanici ? "tarlalarim" : "manuel");
  const [tarlalar, setTarlalar] = useState([]);
  const [secilenTarlalar, setSecilenTarlalar] = useState([]);
  const [manuelForm, setManuelForm] = useState({ ilce: "", donum: "" });
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");

  useEffect(() => {
    if (aktifKullanici) {
      fetch(`http://localhost:8000/tarla/liste?kullanici_id=${aktifKullanici.id}`)
        .then((res) => res.json())
        .then((data) => setTarlalar(Array.isArray(data) ? data : []))
        .catch(() => setTarlalar([]));
    }
  }, []);

  const tarlaSecimiDegistir = (tarlaId) => {
    setSecilenTarlalar((prev) =>
      prev.includes(tarlaId) ? prev.filter((id) => id !== tarlaId) : [...prev, tarlaId]
    );
  };

  const toplamDonum = tarlalar
    .filter((t) => secilenTarlalar.includes(t.id))
    .reduce((sum, t) => sum + Number(t.donum || 0), 0);

  const handleManuelChange = (e) => {
    setManuelForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const oneriAl = async () => {
    setHata("");

    let payload;
    if (mod === "tarlalarim") {
      if (secilenTarlalar.length === 0) {
        setHata("Lütfen en az bir tarla seç.");
        return;
      }
      payload = { mod: "tarlalarim", tarla_idleri: secilenTarlalar, toplam_donum: toplamDonum };
    } else {
      if (!manuelForm.ilce || !manuelForm.donum) {
        setHata("Lütfen ilçe ve dönüm bilgisini doldur.");
        return;
      }
      payload = { mod: "manuel", ilce: manuelForm.ilce, donum: manuelForm.donum };
    }

    setYukleniyor(true);
    setSonuc(null);
    try {
      const res = await fetch("http://localhost:8000/oneri/getir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok) {
        setSonuc(data);
      } else {
        setHata(data.detail || "Öneri alınamadı.");
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
        <span className="eyebrow">Öneri Sistemi</span>
        <h2>Ekim Planı Önerisi</h2>
      </div>

      <div className="analysis-grid">
        <div className="panel">
          <h3>Kaynak Seç</h3>

          <div className="source-toggle">
            <button
              type="button"
              className={mod === "tarlalarim" ? "active" : ""}
              onClick={() => setMod("tarlalarim")}
            >
              Tarlalarımdan Seç
            </button>
            <button
              type="button"
              className={mod === "manuel" ? "active" : ""}
              onClick={() => setMod("manuel")}
            >
              Kendim Girmek İstiyorum
            </button>
          </div>

          {mod === "tarlalarim" ? (
            !aktifKullanici ? (
              <div className="empty-state">
                Kayıtlı tarlalarını kullanabilmek için önce giriş yapmalısın.
              </div>
            ) : tarlalar.length === 0 ? (
              <div className="empty-state">
                Henüz kayıtlı tarlan yok. "Tarlalarım" sayfasından tarla ekleyebilirsin.
              </div>
            ) : (
              <>
                <div className="tarla-picklist">
                  {tarlalar.map((t) => (
                    <label className="tarla-pick-item" key={t.id}>
                      <input
                        type="checkbox"
                        checked={secilenTarlalar.includes(t.id)}
                        onChange={() => tarlaSecimiDegistir(t.id)}
                      />
                      <div className="info">
                        <strong>{t.ad}</strong>
                        <span>{t.ilce} · {t.donum} dönüm</span>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="toplam-donum-box">Toplam Dönüm: {toplamDonum || 0}</div>
              </>
            )
          ) : (
            <>
              <div className="field">
                <label>İlçe</label>
                <select name="ilce" value={manuelForm.ilce} onChange={handleManuelChange}>
                  <option value="">İlçe seç</option>
                  {ILCELER.map((i) => (
                    <option key={i} value={i}>{i}</option>
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
                  placeholder="Örn. 10"
                  value={manuelForm.donum}
                  onChange={handleManuelChange}
                />
              </div>
            </>
          )}

          {hata && <div className="form-message error">{hata}</div>}

          <button className="run-btn" onClick={oneriAl} disabled={yukleniyor}>
            {yukleniyor ? "Hesaplanıyor..." : "Öneri Al"}
          </button>
        </div>

        <div className="results-column">
          {sonuc ? (
            <>
              <div className="oneri-grid">
                {sonuc.oneriler?.map((o, idx) => (
                  <div className="oneri-cell" key={idx}>
                    <div className="donum">{o.donum} dönüm</div>
                    <div className="urun">{o.urun}</div>
                  </div>
                ))}
              </div>
              <div className="result-row">
                <div className="result-card highlight">
                  <div className="label">Tahmini Kâr</div>
                  <div className="value">{sonuc.tahmini_kar} ₺</div>
                </div>
                <div className="result-card">
                  <div className="label">Toplam Risk Skoru</div>
                  <div className="value">%{sonuc.risk_skoru}</div>
                </div>
              </div>
            </>
          ) : (
            <div className="panel">
              <div className="empty-state">
                Bir kaynak seç ve "Öneri Al" butonuna bas — tarlan için önerilen ekim
                dağılımı burada görünecek.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Recommendations;
