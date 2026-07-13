import { Link, useLocation } from "react-router-dom";

function Navbar() {
  const location = useLocation();
  const kayit = localStorage.getItem("kullanici");
  const aktifKullanici = kayit ? JSON.parse(kayit) : null;

  const cikisYap = () => {
    localStorage.removeItem("kullanici");
    window.location.href = "/";
  };

  const isActive = (path) => (location.pathname === path ? "active" : "");

  return (
    <header className="navbar">
      <div className="brand">
        <Link to="/">
          <h2>
            Tarım <span>Analiz</span>
          </h2>
        </Link>
      </div>

      <nav className="nav-links">
        <Link to="/" className={isActive("/")}>
          Ana Sayfa
        </Link>
        <Link to="/fiyat-tahmini" className={isActive("/fiyat-tahmini")}>
          Fiyat Tahmini
        </Link>
        <Link to="/kar-hesabi" className={isActive("/kar-hesabi")}>
          Kâr Hesabı
        </Link>
        <Link to="/risk-analizi" className={isActive("/risk-analizi")}>
          Risk Analizi
        </Link>
        <Link to="/oneriler" className={isActive("/oneriler")}>
          Öneri Sistemi
        </Link>

        <div className="nav-auth">
          {aktifKullanici ? (
            <div className="nav-profile" tabIndex={0}>
              <div className="chip">
                👤 {aktifKullanici.ad}
                <span className="caret">▾</span>
              </div>
              <div className="dropdown-menu">
                <Link to="/bilgilerim">Kişisel Bilgilerim</Link>
                <Link to="/tarlalarim">Tarlalarım</Link>
                <div className="menu-divider" />
                <button className="logout-item" onClick={cikisYap}>
                  Çıkış Yap
                </button>
              </div>
            </div>
          ) : (
            <Link to="/login" className="btn btn-primary">
              Giriş Yap
            </Link>
          )}
        </div>
      </nav>
    </header>
  );
}

export default Navbar;