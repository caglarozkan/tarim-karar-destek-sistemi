import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Login from "./pages/Login.jsx";
import "./App.css";

function Home() {
  const features = [
    {
      title: "Fiyat Tahmini",
      text: "Geçmiş hal fiyatlarına göre ürünlerin olası fiyat değişimini analiz eder.",
    },
    {
      title: "Kâr Hesabı",
      text: "Mazot, gübre, sulama ve işçilik maliyetlerine göre tahmini kârlılığı hesaplar.",
    },
    {
      title: "Risk Skoru",
      text: "Ürünün arz, fiyat dalgalanması ve tarlada kalma riskini değerlendirir.",
    },
    {
      title:"Öneri Sistemi",
      text:"Dönüm bilgisine göre en uygun ekim planını sunar."
    }
  ];

  return (
    <div className="page">
      <header className="navbar">
        <div className="brand">
          <h2>Tarım Analiz Sistemi</h2>
        </div>

        <nav className="nav-links">
          <Link to="/">Ana Sayfa</Link>
          <a href="#analysis">Analiz</a>
          <a href="#recommendations">Öneriler</a>
          <Link to="/login">Giriş</Link>
        </nav>
      </header>

      <main>
        <section className="hero" id="home">
          <div className="hero-content">
            <span className="hero-label">Veriye dayalı üretim kararı</span>

            <h1>Akıllı Tarım Ürün Öneri Platformu</h1>

            <p>
              Bölge, ürün, maliyet ve hal fiyatı verilerine göre daha doğru
              üretim kararları alın.
            </p>

            <div className="hero-actions">
              <button type="button" className="primary-button">
                Analize Başla
              </button>
            </div>
          </div>
        </section>

        <section className="cards" id="analysis">
          {features.map((feature) => (
            <article className="card" key={feature.title}>
              <h3>{feature.title}</h3>
              <p>{feature.text}</p>
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;