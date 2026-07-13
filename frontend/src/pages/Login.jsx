import { useState } from "react";
import "../App.css";

function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [mesaj, setMesaj] = useState({ text: "", type: "" });
  const [form, setForm] = useState({
    ad_soyad: "",
    email: "",
    password: "",
    passwordConfirm: "",
    yas: "",
    cinsiyet: "",
    telefon: "",
  });

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
    setMesaj({ text: "", type: "" });
  };

  const switchTab = (login) => {
    setIsLogin(login);
    setMesaj({ text: "", type: "" });
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setMesaj({ text: "", type: "" });

    if (!form.email || !form.password || (!isLogin && (!form.ad_soyad || !form.passwordConfirm))) {
      setMesaj({ text: "Lütfen tüm alanları doldur.", type: "error" });
      return;
    }

    if (!isLogin && form.password !== form.passwordConfirm) {
      setMesaj({ text: "Şifreler uyuşmuyor!", type: "error" });
      return;
    }

    const url = `http://localhost:8000${isLogin ? "/kullanici/giris" : "/kullanici/kayit"}`;
    const payload = isLogin
      ? { email: form.email, sifre: form.password }
      : {
          ad_soyad: form.ad_soyad,
          email: form.email,
          sifre: form.password,
          yas: form.yas || null,
          cinsiyet: form.cinsiyet || null,
          telefon: form.telefon || null,
        };

    try {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (res.ok) {
        if (isLogin) {
          localStorage.setItem(
            "kullanici",
            JSON.stringify({
              id: data.kullanici_id,
              ad: data.ad_soyad,
              email: form.email,
              yas: data.yas ?? null,
              cinsiyet: data.cinsiyet ?? null,
              telefon: data.telefon ?? null,
            })
          );
          setMesaj({ text: "Giriş başarılı!", type: "success" });
          setTimeout(() => {
            window.location.href = "/";
          }, 1200);
        } else {
          setMesaj({ text: "Kayıt başarılı! Şimdi giriş yapabilirsin.", type: "success" });
          setTimeout(() => switchTab(true), 1500);
        }
      } else {
        setMesaj({ text: data.detail || "Bir hata oluştu.", type: "error" });
      }
    } catch (err) {
      setMesaj({ text: "Sunucuya bağlanılamadı.", type: "error" });
    }
  };

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-header">
          <div className="tab-switch">
            <button type="button" className={isLogin ? "active" : ""} onClick={() => switchTab(true)}>
              Giriş Yap
            </button>
            <button type="button" className={!isLogin ? "active" : ""} onClick={() => switchTab(false)}>
              Kayıt Ol
            </button>
          </div>
          <h1>{isLogin ? "Tekrar hoş geldin" : "Hesap oluştur"}</h1>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {!isLogin && (
            <label>
              Ad Soyad
              <input type="text" name="ad_soyad" value={form.ad_soyad} onChange={handleChange} />
            </label>
          )}
          {!isLogin && (
            <label>
              Yaş
              <input
                type="number"
                min="0"
                name="yas"
                placeholder="Opsiyonel"
                value={form.yas}
                onChange={handleChange}
              />
            </label>
          )}
          {!isLogin && (
            <label>
              Cinsiyet
              <select name="cinsiyet" value={form.cinsiyet} onChange={handleChange}>
                <option value="">Belirtmek istemiyorum</option>
                <option value="Kadın">Kadın</option>
                <option value="Erkek">Erkek</option>
                <option value="Diğer">Diğer</option>
              </select>
            </label>
          )}
          {!isLogin && (
            <label>
              Telefon No
              <input
                type="tel"
                name="telefon"
                placeholder="05xx xxx xx xx"
                value={form.telefon}
                onChange={handleChange}
              />
            </label>
          )}
          <label>
            E-posta
            <input type="email" name="email" value={form.email} onChange={handleChange} />
          </label>
          <label>
            Şifre
            <input type="password" name="password" value={form.password} onChange={handleChange} />
          </label>
          {!isLogin && (
            <label>
              Şifre (Tekrar)
              <input
                type="password"
                name="passwordConfirm"
                value={form.passwordConfirm}
                onChange={handleChange}
              />
            </label>
          )}

          {mesaj.text && <div className={`form-message ${mesaj.type}`}>{mesaj.text}</div>}

          <button type="submit">{isLogin ? "Giriş Yap" : "Kaydı Tamamla"}</button>
        </form>
      </section>
    </main>
  );
}

export default Login;
