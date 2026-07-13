import { Link } from "react-router-dom";
import "../App.css";

const features = [
  {
    title: "Fiyat Tahmini",
    text: "Geçmiş hal fiyatlarına göre ürünlerin olası fiyat değişimini analiz eder.",
    link: "/fiyat-tahmini",
  },
  {
    title: "Kâr Hesabı",
    text: "Mazot, gübre, sulama ve işçilik maliyetlerine göre tahmini kârlılığı hesaplar.",
    link: "/kar-hesabi",
  },
  {
    title: "Risk Skoru",
    text: "Ürünün arz, fiyat dalgalanması ve tarlada kalma riskini değerlendirir.",
    link: "/risk-analizi",
  },
  {
    title: "Öneri Sistemi",
    text: "Tarlalarından ya da girdiğin dönüm bilgisinden yola çıkarak en uygun ekim planını önerir.",
    link: "/oneriler",
  },
];

function Home() {
  return (
    <div className="page">
      <main>
        <section className="hero">
          <div className="hero-content">
            <h1>Akıllı Tarım Ürün Öneri Platformu</h1>
            <p>
              İlçe, ürün ve sezon bilgine göre fiyat, kâr ve risk tahmini yap; çiftçilik
              kararlarını verilerle destekle.
            </p>
          </div>
        </section>

        <section className="home-section">
          <div className="section-title">
            <h2>Neler Yapabilirsin?</h2>
            <p>Aşağıdaki analizlerden istediğini seçerek hemen başla.</p>
          </div>
          <div className="cards">
            {features.map((feature) => (
              <Link to={feature.link} className="card" key={feature.title}>
                <h3>{feature.title}</h3>
                <p>{feature.text}</p>
              </Link>
            ))}
          </div>
        </section>
      </main>
    </div>
  );
}

export default Home;
