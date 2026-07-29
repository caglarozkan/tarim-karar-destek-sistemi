import { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = [
  "#2E7D32", // yeşil
  "#F2C94C", // sarı
  "#2D9CDB", // mavi
  "#F2994A", // turuncu
  "#9B51E0", // mor
  "#EB5757", // kırmızı
  "#56CCF2", // açık mavi
  "#6FCF97", // mint
  "#BB6BD9", // lila
  "#F08080", // mercan
];

function MyProducts() {
  const [urunler, setUrunler] = useState([]);
  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");

  const kayit = localStorage.getItem("kullanici");
  const kullanici = kayit ? JSON.parse(kayit) : null;


  useEffect(() => {
    if (!kullanici) return;

    urunleriGetir();
  }, []);


  const urunleriGetir = async () => {
    try {
      const res = await fetch(
        `http://localhost:8000/urunlerim/${kullanici.id}`
      );
      if (!res.ok){
          throw new Error()
      }
      const data = await res.json();
      setUrunler(data);

    } catch (err) {
      setHata("Sunucuya bağlanılamadı.");
    }
      finally {
      setYukleniyor(false);
      }
  };

  const toplamAlan=urunler.reduce(
      (toplam,urun) =>
      toplam+urun.toplam_donum,
      0
  );

  if (yukleniyor) {
    return (
      <div className="page-container">
        <div className="empty-state">
          Yükleniyor...
        </div>
      </div>
    );

  }
  if (hata) {
    return (
      <div className="page-container">
        <div className="form-message error">
          {hata}
        </div>
      </div>
    );

  }
  return (
    <div className="page-container">
      <div className="analysis-header">
        <span className="eyebrow">
          Ürünlerim
        </span>
        <h2>
          Kayıtlı Ürünler
        </h2>
      </div>
      <div className="products-layout">

        <div className="products-list">
          {urunler.map((urun, index) => {
            const maxDonum = Math.max(
              ...urun.tarlalar.map(
                t => t.donum
              )
            );

            return (
              <div
                className="product-card"
                key={urun.urun_adi}
              >
                <div className="product-header">
                  <h3>
                    {index === 0 && "🥇 "}
                    {index === 1 && "🥈 "}
                    {index === 2 && "🥉 "}
                    {index + 1}. {urun.urun_adi}
                  </h3>
                  <div className="product-total">
                    {urun.toplam_donum} dönüm

                  </div>
                </div>
                <div className="product-info">
                  {urun.tarlalar.map((tarla) => {
                    const width =
                      (tarla.donum / maxDonum) * 100;
                    return (
                      <div
                        className="field-progress"
                        key={tarla.tarla_adi}
                      >
                        <div className="field-top">
                          <span>
                            {tarla.tarla_adi}
                          </span>
                          <span>
                            {tarla.donum} dönüm
                          </span>
                        </div>
                        <div className="progress-background">
                          <div
                            className="progress-fill"
                            style={{
                              width: `${width}%`
                            }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
<div className="products-chart">
  <h3>Alan Dağılımı</h3>

  <ResponsiveContainer width="100%" height={360}>
    <PieChart>
      <Pie
        data={urunler}
        dataKey="toplam_donum"
        nameKey="urun_adi"
        cx="50%"
        cy="42%"
        outerRadius={90}
        label={false}
      >
        {urunler.map((entry, index) => (
          <Cell
            key={`cell-${index}`}
            fill={COLORS[index % COLORS.length]}
          />
        ))}
      </Pie>

      <Tooltip
        formatter={(value, name) => [`${value} dönüm`, name]}
      />

      <Legend
        layout="horizontal"
        verticalAlign="bottom"
        align="center"
        wrapperStyle={{
          fontSize: "13px",
          lineHeight: "20px",
          paddingTop: "12px",
        }}
      />
    </PieChart>
  </ResponsiveContainer>

  <div className="total-area">
    Toplam Alan: <b>{toplamAlan} dönüm</b>
  </div>
</div>
      </div>
    </div>
  );
}

export default MyProducts;