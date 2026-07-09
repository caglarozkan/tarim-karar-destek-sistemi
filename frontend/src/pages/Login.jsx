import { useState } from "react";
import { useNavigate } from "react-router-dom";
import "../App.css";

function Login() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    email: "",
    password: "",
  });

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((prevForm) => ({
      ...prevForm,
      [name]: value,
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();

    if (!form.email || !form.password) {
      alert("Lütfen e-posta ve şifre alanlarını doldurun.");
      return;
    }

    // Şimdilik örnek giriş. Backend bağlanınca burası API isteği olacak.
    navigate("/dashboard");
  };

  return (
    <main className="login-page">
      <section className="login-card">
        <div className="login-header">
          <h1>Giriş Yap</h1>
          <p>Tarım Analiz Sistemi paneline erişin.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <label>
            E-posta
            <input
              type="email"
              name="email"
              placeholder="ornek@mail.com"
              value={form.email}
              onChange={handleChange}
            />
          </label>

          <label>
            Şifre
            <input
              type="password"
              name="password"
              placeholder="Şifrenizi girin"
              value={form.password}
              onChange={handleChange}
            />
          </label>

          <button type="submit">Giriş Yap</button>
        </form>
      </section>
    </main>
  );
}

export default Login;