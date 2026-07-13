import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";

function Profile() {
  const navigate = useNavigate();
  const [kullanici, setKullanici] = useState(null);
  const [duzenleAcik, setDuzenleAcik] = useState(false);
  const [form, setForm] = useState({ ad_soyad: "", yas: "", cinsiyet: "", telefon: "" });
  const [mesaj, setMesaj] = useState({ text: "", type: "" });

  useEffect(() => {
    const kayit = localStorage.getItem("kullanici");
    if (!kayit) {
      navigate("/login");
      return;
    }
    const user = JSON.parse(kayit);
    setKullanici(user);
    setForm({ ad_soyad: user.ad || "", yas: user.yas || "", cinsiyet: user.cinsiyet || "", telefon: user.telefon || "" });

    // Backend'de kullanıcının en güncel bilgisini tutan bir endpoint varsa
    // (ör. GET /kullanici/:id) burada çekip localStorage'daki veriyi tazeleyebilirsin.
    fetch(`http://localhost:8000/kullanici/${user.id}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) {
          const guncel = { ...user, ...data };
          setKullanici(guncel);
          setForm({ ad_soyad: guncel.ad || guncel.ad_soyad || "", yas: guncel.yas || "", cinsiyet: guncel.cinsiyet || "", telefon: guncel.telefon || "" });
          localStorage.setItem("kullanici", JSON.stringify(guncel));
        }
      })
      .catch(() => {
        /* endpoint henüz yoksa localStorage'daki bilgiyle devam edilir */
      });
  }, [navigate]);

  const handleChange = (e) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const kaydet = async (e) => {
    e.preventDefault();
    setMesaj({ text: "", type: "" });
    try {
      const res = await fetch("http://localhost:8000/kullanici/guncelle", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ kullanici_id: kullanici.id, ...form }),
      });
      const data = await res.json();
      if (res.ok) {
        const guncel = { ...kullanici, ad: form.ad_soyad, yas: form.yas, cinsiyet: form.cinsiyet, telefon: form.telefon };
        setKullanici(guncel);
        localStorage.setItem("kullanici", JSON.stringify(guncel));
        setMesaj({ text: "Bilgilerin güncellendi.", type: "success" });
        setDuzenleAcik(false);
      } else {
        setMesaj({ text: data.detail || "Güncellenemedi.", type: "error" });
      }
    } catch (err) {
      setMesaj({ text: "Sunucuya bağlanılamadı.", type: "error" });
    }
  };

  if (!kullanici) return null;

  return (
    <div className="page-container">
      <div className="farms-toolbar">
        <div className="analysis-header" style={{ marginBottom: 0 }}>
          <span className="eyebrow">Hesabım</span>
          <h2>Kişisel Bilgilerim</h2>
        </div>
        <button className="btn btn-primary" onClick={() => setDuzenleAcik((v) => !v)}>
          {duzenleAcik ? "Vazgeç" : "Bilgilerimi Düzenle"}
        </button>
      </div>

      {mesaj.text && <div className={`form-message ${mesaj.type}`} style={{ marginBottom: 16 }}>{mesaj.text}</div>}

      {duzenleAcik ? (
        <form className="profile-edit-form" onSubmit={kaydet}>
          <div className="field">
            <label>Ad Soyad</label>
            <input type="text" name="ad_soyad" value={form.ad_soyad} onChange={handleChange} />
          </div>
          <div className="field">
            <label>Yaş</label>
            <input type="number" min="0" name="yas" value={form.yas} onChange={handleChange} />
          </div>
          <div className="field">
            <label>Cinsiyet</label>
            <select name="cinsiyet" value={form.cinsiyet} onChange={handleChange}>
              <option value="">Belirtmek istemiyorum</option>
              <option value="Kadın">Kadın</option>
              <option value="Erkek">Erkek</option>
              <option value="Diğer">Diğer</option>
            </select>
          </div>
          <div className="field">
            <label>Telefon No</label>
            <input type="tel" name="telefon" placeholder="05xx xxx xx xx" value={form.telefon} onChange={handleChange} />
          </div>
          {/* Yeni bir bilgi alanı eklemek için: 1) buraya bir .field bloğu daha ekle,
              2) yukarıdaki form state'ine ve handleChange'in kapsadığı name'e ekle,
              3) kaydet() içindeki payload otomatik olarak taşır. */}
          <div className="profile-edit-actions">
            <button type="submit" className="btn btn-primary">Kaydet</button>
          </div>
        </form>
      ) : (
        <div className="info-grid">
          <div className="info-item">
            <div className="label">Ad Soyad</div>
            <div className="value">{kullanici.ad}</div>
          </div>
          <div className="info-item">
            <div className="label">E-posta</div>
            <div className="value">{kullanici.email || "-"}</div>
          </div>
          <div className="info-item">
            <div className="label">Yaş</div>
            <div className="value">{kullanici.yas || "-"}</div>
          </div>
          <div className="info-item">
            <div className="label">Cinsiyet</div>
            <div className="value">{kullanici.cinsiyet || "-"}</div>
          </div>
          <div className="info-item">
            <div className="label">Telefon No</div>
            <div className="value">{kullanici.telefon || "-"}</div>
          </div>
          <div className="info-item">
            <div className="label">Kullanıcı No</div>
            <div className="value">{kullanici.id}</div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Profile;
