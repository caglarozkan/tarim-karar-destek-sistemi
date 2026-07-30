import { useEffect, useMemo, useRef, useState } from "react";

function Statistics() {
  const [fiyatlar, setFiyatlar] = useState([]);
  const [arama, setArama] = useState("");
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");
  const [veriTarihi, setVeriTarihi] = useState("");

  const isFetched = useRef(false);

  useEffect(() => {
    if (isFetched.current) {
      return;
    }

    isFetched.current = true;

    const halFiyatlariniGetir = async () => {
      try {
        setYukleniyor(true);
        setHata("");

        const res = await fetch("http://localhost:8000/istatistikler/hal-fiyatlari");

        if (!res.ok) {
          throw new Error("Hal fiyatları alınamadı.");
        }

        const data = await res.json();
        const gelenFiyatlar = Array.isArray(data.prices) ? data.prices : [];

        setFiyatlar(gelenFiyatlar);
        setVeriTarihi(data.date || "");
      } catch {
        setHata("Hal fiyatları yüklenemedi.");
      } finally {
        setYukleniyor(false);
      }
    };

    halFiyatlariniGetir();
  }, []);

  const filtrelenmisFiyatlar = useMemo(() => {
    const temizArama = arama.toLowerCase().trim();

    if (!temizArama) {
      return fiyatlar;
    }

    return fiyatlar.filter((item) => (
      item.product_name?.toLowerCase().includes(temizArama) ||
      item.type?.toLowerCase().includes(temizArama) ||
      item.unit?.toLowerCase().includes(temizArama)
    ));
  }, [arama, fiyatlar]);

  if (yukleniyor) {
    return (
      <div className="page-container">
        <div className="empty-state">Hal fiyatları yükleniyor...</div>
      </div>
    );
  }

  if (hata && fiyatlar.length === 0) {
    return (
      <div className="page-container">
        <div className="form-message error">{hata}</div>
      </div>
    );
  }

  return (
    <div className="page-container">
      <div className="analysis-header">
        <span className="eyebrow">İstatistikler</span>
        <h2>Günlük Hal Fiyatları</h2>

        {veriTarihi && (
          <p className="statistics-date">
            Veri tarihi: <strong>{veriTarihi}</strong>
          </p>
        )}
      </div>

      <div className="statistics-toolbar">
        <input
          type="text"
          value={arama}
          onChange={(e) => setArama(e.target.value)}
          placeholder="Ürün ara..."
          className="statistics-search"
        />
      </div>

      <div className="price-table-card">
        <table className="price-table">
          <thead>
            <tr>
              <th>Tip</th>
              <th>Ürün Adı</th>
              <th>Birim</th>
              <th>En Az</th>
              <th>En Çok</th>
              <th>Ortalama</th>
            </tr>
          </thead>

<tbody>
  {filtrelenmisFiyatlar.map((item, index) => (
    <tr key={`${item.product_name}-${index}`}>
      <td>{item.type}</td>
      <td>{item.product_name}</td>
      <td>{item.unit}</td>
      <td>
        {item.min_price !== null ? `${Number(item.min_price).toFixed(2)} TL` : "-"}
      </td>
      <td>
        {item.max_price !== null ? `${Number(item.max_price).toFixed(2)} TL` : "-"}
      </td>
      <td>
        {item.average_price !== null ? `${Number(item.average_price).toFixed(2)} TL` : "-"}
      </td>
      <td>
        <span className={item.price_found ? "price-status current" : "price-status missing"}>
          {item.note}
        </span>
      </td>
    </tr>
  ))}
</tbody>
        </table>

        {filtrelenmisFiyatlar.length === 0 && (
          <div className="empty-state">Gösterilecek ürün bulunamadı.</div>
        )}
      </div>
    </div>
  );
}

export default Statistics;