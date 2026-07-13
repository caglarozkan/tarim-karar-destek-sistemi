import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";

const ILCELER = ["Bayındır", "Ödemiş", "Tire", "Kiraz", "Bergama"];
const URUNLER = ["Domates", "Patates", "Soğan", "Biber", "Salatalık"];

function Farms() {
  const navigate = useNavigate();
  const [kullanici, setKullanici] = useState(null);
  const [tarlalar, setTarlalar] = useState([]);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");
  const [formAcik, setFormAcik] = useState(false);
  const [form, setForm] = useState({ ad: "", ilce: "", urun: "", donum: "" });

  useEffect(() => {
    const kayit = localStorage.getItem("kullanici");
    if (!kayit) {
      navigate("/login");
      return;
    }
    const user = JSON.parse(kayit);
    setKullanici(user);
    tarlalariGetir(user.id);
  }, [navigate]);

  const tarlalariGetir = async (kullaniciId) => {
    setYukleniyor(true);
    setHata("");
    try {
      const res = await fetch(`http://localhost:8000/tarla/liste?kullanici_id=${kullaniciId}`);
      const data = await res.json();
      if (res.ok) {
        setTarlalar(data);
      } else {
        setHata(data.detail || "Tarlalar alınamadı.");
      }
    } catch (err) {
      setHata("Sunucuya bağlanılamadı.");
    } finally {
      setYukleniyor(false);
    }
  };

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const tarlaEkle = async (e) => {
    e.preventDefault();
    if (!form.ad || !form.ilce || !form.urun || !form.donum) {
      setHata("Lütfen tüm alanları doldur.");
      return;
    }
    try {
      const res = await fetch("http://localhost:8000/tarla/ekle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...form, kullanici_id: kullanici.id }),
      });
      const data = await res.json();
      if (res.ok) {
        setForm({ ad: "", ilce: "", urun: "", donum: "" });
        setFormAcik(false);
        tarlalariGetir(kullanici.id);
      } else {
        setHata(data.detail || "Tarla eklenemedi.");
      }
    } catch (err) {
      setHata("Sunucuya bağlanılamadı.");
    }
  };

  return (
    <div className="page-container">
      <div className="farms-toolbar">
        <div className="analysis-header" style={{ marginBottom: 0 }}>
          <span className="eyebrow">Tarlalarım</span>
          <h2>Kayıtlı Tarlalar</h2>
        </div>
        <button className="btn btn-primary" onClick={() => setFormAcik((v) => !v)}>
          {formAcik ? "Vazgeç" : "+ Yeni Tarla Ekle"}
        </button>
      </div>

      {hata && <div className="form-message error" style={{ marginBottom: 16 }}>{hata}</div>}

      {formAcik && (
        <form className="new-farm-form" onSubmit={tarlaEkle}>
          <div className="field">
            <label>Tarla Adı</label>
            <input type="text" name="ad" value={form.ad} onChange={handleChange} placeholder="Örn. Alt Tarla" />
          </div>
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
                <option key={u} value={u}>{u}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Dönüm</label>
            <input type="number" min="0" step="0.1" name="donum" value={form.donum} onChange={handleChange} />
          </div>
          <button type="submit" className="run-btn" style={{ alignSelf: "end" }}>
            Kaydet
          </button>
        </form>
      )}

      {yukleniyor ? (
        <div className="empty-state">Tarlalar yükleniyor...</div>
      ) : tarlalar.length === 0 ? (
        <div className="panel">
          <div className="empty-state">Henüz kayıtlı bir tarlan yok. "+ Yeni Tarla Ekle" ile başla.</div>
        </div>
      ) : (
        <div className="farms-list">
          {tarlalar.map((t) => (
            <div className="farm-card" key={t.id}>
              <h4>{t.ad}</h4>
              <div className="meta">İlçe: {t.ilce}</div>
              <div className="meta">Ürün: {t.urun}</div>
              <div className="meta">Dönüm: {t.donum}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Farms;
