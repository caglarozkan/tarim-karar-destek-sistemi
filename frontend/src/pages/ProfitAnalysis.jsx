import { useState, useEffect } from "react";
import "../App.css";

const ILCELER = ["Bayındır","Bergama","Menderes","Tire","Torbalı","Ödemiş"];
const URUNLER = ["Biber (Sivri)","Domates (Sofralık)","Hıyar (Sofralık)","Kabak (Sakız)","Karpuz","Patlıcan","Soğan (Kuru)"];
const SEZONLAR = ["İlkbahar", "Yaz", "Sonbahar", "Kış"];

function ProfitAnalysis() {
  const [form, setForm] = useState({
    ilce: "",
    urun: "",
    donum: "",
    sezon: "",
    sulama_maliyeti: "",
    iscilik_maliyeti: "",
    tohum_maliyeti: "",
  });
  const [kullanici,setKullanici]=useState(null);
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");

  useEffect(() => {
      const kayit = localStorage.getItem("kullanici");
      if ( kayit) setKullanici(JSON.parse(kayit));
      },[]);

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
        setHata("Önce giriş yapmalısın!");
        return;
    }

    setYukleniyor(true);
    setSonuc(null);
    try {
      const res = await fetch("http://localhost:8000/kar/hesapla", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({...form,kullanici_id:kullanici.id}),
      });
      const data = await res.json();
      if (res.ok) {
         setSonuc(data);
      } else {
          const mesaj = typeof data.detail ==="string" ? data.detail : "Tahmin alınamadı";
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
        <span className="eyebrow">Kâr Hesabı</span>
        <h2>Tahmini Kârlılık Analizi</h2>
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
            <label>Ürün Seçimi</label>
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

          <div className="optional-block">
            <span className="optional-label">Opsiyonel Maliyetler</span>

            <div className="field">
              <label>Sulama Maliyeti (₺)</label>
              <input
                type="number"
                min="0"
                name="sulama_maliyeti"
                placeholder="Bilinmiyorsa boş bırak"
                value={form.sulama_maliyeti}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>İşçilik Maliyeti (₺)</label>
              <input
                type="number"
                min="0"
                name="iscilik_maliyeti"
                placeholder="Bilinmiyorsa boş bırak"
                value={form.iscilik_maliyeti}
                onChange={handleChange}
              />
            </div>

            <div className="field">
              <label>Tohum Maliyeti (₺)</label>
              <input
                type="number"
                min="0"
                name="tohum_maliyeti"
                placeholder="Bilinmiyorsa boş bırak"
                value={form.tohum_maliyeti}
                onChange={handleChange}
              />
            </div>
          </div>

          {hata && <div className="form-message error">{hata}</div>}

          <button className="run-btn" onClick={analiziBaslat} disabled={yukleniyor}>
            {yukleniyor ? "Hesaplanıyor..." : "Analizi Başlat"}
          </button>
        </div>

        <div className="results-column">
          {sonuc ? (
            <>
              <>
  <div className="result-row">
    <div className="result-card">
      <div className="label">Tahmini Üretim</div>
      <div className="value">{sonuc.tahmini_uretim} ton</div>
    </div>

    <div className="result-card">
      <div className="label">Tahmini Fiyat</div>
      <div className="value">{sonuc.tahmini_fiyat} ₺/kg</div>
    </div>
  </div>

  <div className="result-row">
    <div className="result-card">
      <div className="label">Tahmini Gelir</div>
      <div className="value">{sonuc.tahmini_gelir.toLocaleString()} ₺</div>
    </div>

    <div className="result-card">
      <div className="label">Toplam Gider</div>
      <div className="value">{sonuc.toplam_gider.toLocaleString()} ₺</div>
    </div>
  </div>

  <div className="panel" style={{marginTop:"15px"}}>

    <h3>Maliyet Detayları</h3>

    <div className="field">
      <label>Gübre Gideri</label>
      <strong>{sonuc.gubre_gideri.toLocaleString()} ₺</strong>
    </div>

    <div className="field">
      <label>Mazot Gideri</label>
      <strong>{sonuc.mazot_gideri.toLocaleString()} ₺</strong>
    </div>

    <div className="field">
      <label>Ek Giderler</label>
      <strong>{sonuc.ek_giderler.toLocaleString()} ₺</strong>
    </div>
  </div>

  <div className="result-card highlight" style={{marginTop:"20px"}}>
    <div className="label">Tahmini Net Kâr</div>
    <div className="value">{sonuc.net_kar.toLocaleString()} ₺</div>
  </div>
</>
            </>
          ) : (
            <div className="panel">
              <div className="empty-state">
                Tarla bilgilerini doldur — tahmini gelir, gider ve kâr burada görünecek.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfitAnalysis;
