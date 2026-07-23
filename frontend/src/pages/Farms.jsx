import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";
import { URUNLER, URUN_GORUNEN_ADLAR } from "../constants/urunler";

function Farms() {
  const navigate = useNavigate();
  const [kullanici, setKullanici] = useState(null);

  const [ilceler, setIlceler] = useState([]); //backend'den gelecek ilce ad ilce_id
  const [urunler, setUrunler] = useState([]); //backend'den gelecek ürün_id ürünad
  const [tarlalar, setTarlalar] = useState([]);

  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");
  const [formAcik, setFormAcik] = useState(false);

  const [tarlaAdi, setTarlaAdi] = useState("");
  const [ilceId, setIlceId] = useState("");
  const [urunSatirlari, setUrunSatirlari] = useState([{ urun_id: "", donum: "" }]);

  useEffect(() => {
    const kayit = localStorage.getItem("kullanici");
    if (!kayit) {
      navigate("/login");
      return;
    }
    const user = JSON.parse(kayit);
    setKullanici(user);
    baslangicVerileriniGetir(user.id);
  }, [navigate]);

  // Sayfa açılınca: ilçe listesi + ürün listesi + kullanıcının tarlaları
  const baslangicVerileriniGetir = async (kullaniciId) => {
    setYukleniyor(true);
    setHata("");
    try {
      const ilceRes = await fetch("http://localhost:8000/ilce/liste");
      setIlceler(await ilceRes.json());

      const urunRes = await fetch("http://localhost:8000/urun/liste");
      setUrunler(await urunRes.json());

      await tarlalariGetir(kullaniciId);
    } catch (err) {
      setHata("Sunucuya bağlanılamadı.");
    } finally {
      setYukleniyor(false);
    }
  };

  const tarlalariGetir = async (kullaniciId) => {
    const res = await fetch(`http://localhost:8000/tarla/liste?kullanici_id=${kullaniciId}`);
    const data = await res.json();
    setTarlalar(data);
  };

  const satirGuncelle = (index, alan, deger) => {
    const yeniSatirlar = [...urunSatirlari];
    yeniSatirlar[index] = { ...yeniSatirlar[index], [alan]: deger };
    setUrunSatirlari(yeniSatirlar);
  };

  const urunSatiriEkle = () => {
    setUrunSatirlari([...urunSatirlari, { urun_id: "", donum: "" }]);
  };

  const satirSil = (index) => {
    if (urunSatirlari.length === 1) return;
    setUrunSatirlari(urunSatirlari.filter((_, i) => i !== index));
  };

  const formuSifirla = () => {
    setTarlaAdi("");
    setIlceId("");
    setUrunSatirlari([{ urun_id: "", donum: "" }]);
    setFormAcik(false);
  };

  const tarlaOlustur = async (e) => {
    e.preventDefault();
    setHata("");

    if (!tarlaAdi || !ilceId) {
      setHata("Tarla adı ve ilçe zorunlu.");
      return;
    }
    const eksikVar = urunSatirlari.some((s) => !s.urun_id || !s.donum);
    if (eksikVar) {
      setHata("Her ürün satırında ürün ve dönüm doldurulmalı.");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/tarla/ekle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kullanici_id: kullanici.id,
          tarla_adi: tarlaAdi,
          ilce_id: Number(ilceId),
          urunler: urunSatirlari.map((s) => ({
            urun_id: Number(s.urun_id),
            donum: Number(s.donum),
          })),
        }),
      });
      const data = await res.json();
      if (res.ok) {
        formuSifirla();
        tarlalariGetir(kullanici.id);
      } else {
        setHata(data.detail || "Tarla eklenemedi.");
      }
    } catch (err) {
      setHata("Sunucuya bağlanılamadı.");
    }
  };

  const tarlaSil = async (tarlaId) => {
    if (!window.confirm("Bu tarlayı silmek istediğine emin misin?")) return;
    try {
      const res = await fetch(`http://localhost:8000/tarla/sil/${tarlaId}`, { method: "DELETE" });
      if (res.ok) {
        tarlalariGetir(kullanici.id);
      } else {
        setHata("Tarla silinemedi.");
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
        <button className="btn btn-primary" onClick={() => (formAcik ? formuSifirla() : setFormAcik(true))}>
          {formAcik ? "Vazgeç" : "+ Yeni Tarla Ekle"}
        </button>
      </div>

      {hata && <div className="form-message error" style={{ marginBottom: 16 }}>{hata}</div>}

      {formAcik && (
        <form className="new-farm-form" onSubmit={tarlaOlustur}>
          <div className="field">
            <label>Tarla Adı</label>
            <input
              type="text"
              value={tarlaAdi}
              onChange={(e) => setTarlaAdi(e.target.value)}
              placeholder="Örn. Çağların Tarlası"
            />
          </div>

          <div className="field">
            <label>İlçe</label>
            <select value={ilceId} onChange={(e) => setIlceId(e.target.value)}>
              <option value="">İlçe seç</option>
              {ilceler.map((i) => (
                <option key={i.ilce_id} value={i.ilce_id}>{i.ilce_adi}</option>
              ))}
            </select>
          </div>

          {urunSatirlari.map((satir, index) => (
            <div key={index} style={{ display: "flex", gap: 8, gridColumn: "1 / -1" }}>
              <div className="field" style={{ flex: 1 }}>
                <label>Ürün</label>
                <select value={satir.urun_id} onChange={(e) => satirGuncelle(index, "urun_id", e.target.value)}>
                  <option value="">Ürün seç</option>
                  {urunler.map((u) => (
                    <option key={u.urun_id} value={u.urun_id}>{URUN_GORUNEN_ADLAR[u.urun_adi] || u.urun_adi}</option>
                  ))}
                </select>
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label>Dönüm</label>
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={satir.donum}
                  onChange={(e) => satirGuncelle(index, "donum", e.target.value)}
                />
              </div>
              {urunSatirlari.length > 1 && (
                <button type="button" className="btn btn-secondary" onClick={() => satirSil(index)} style={{ alignSelf: "end" }}>
                  Sil
                </button>
              )}
            </div>
          ))}

          <button type="button" className="btn btn-secondary" onClick={urunSatiriEkle} style={{ gridColumn: "1 / -1" }}>
            + Ürün Ekle
          </button>

          <button type="submit" className="run-btn" style={{ alignSelf: "end" }}>
            Tarla Oluştur
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
            <div className="farm-card" key={t.tarla_id}>
              <h4>{t.tarla_adi}</h4>
              <div className="meta">İlçe: {t.ilce_adi}</div>
              {t.urunler.map((u, i) => (
                <div className="meta" key={i}>{u.urun_adi}: {u.donum} dönüm</div>
              ))}
              <button className="btn btn-secondary" onClick={() => tarlaSil(t.tarla_id)} style={{ marginTop: 8 }}>
                Sil
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Farms;