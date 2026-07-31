import { useEffect, useState } from "react";
import "../App.css";
import { aktifUrunleriGetir, URUN_GORUNEN_ADLAR } from "../constants/urunler";

const ILCELER = ["Bayındır", "Bergama", "Menderes", "Tire", "Torbalı", "Ödemiş"];
const SEZONLAR = ["İlkbahar", "Yaz", "Sonbahar", "Kış"];

function Recommendations() {
  const kayit = localStorage.getItem("kullanici");
  const aktifKullanici = kayit ? JSON.parse(kayit) : null;

  const [mod, setMod] = useState(aktifKullanici ? "tarlalarim" : "manuel");
  const [tarlalar, setTarlalar] = useState([]);
  const [secilenTarla, setSecilenTarla] = useState(null);
  const [manuelForm, setManuelForm] = useState({ ilce: "", donum: "" });
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");
  const [sezon, setSezon] = useState("");
  const [secilenUrunler, setSecilenUrunler] = useState([]);
  const [onaylaniyor, setOnaylaniyor] = useState(false);
  const [basariMesaji, setBasariMesaji] = useState("");
  const [urunler, setUrunler] = useState([]);

  useEffect(() => {
    if (aktifKullanici?.id) {
      fetch(`http://localhost:8000/tarla/liste?kullanici_id=${aktifKullanici.id}`)
        .then((res) => res.json())
        .then((data) => setTarlalar(Array.isArray(data) ? data : []))
        .catch(() => setTarlalar([]));
    }
  }, [aktifKullanici?.id]);

  useEffect(() => {
  aktifUrunleriGetir().then(setUrunler);
  }, []);

  const tarlaSec = (tarlaId) => {
    setSecilenTarla(tarlaId);
  };

  const urunSecimiDegistir = (urun) => {
    setSecilenUrunler((prev) =>
      prev.includes(urun) ? prev.filter((u) => u !== urun) : [...prev, urun]
    );
  };

  const uygunTarlalar = tarlalar.filter((t) => t.bos_donum > 0);

  const toplamDonum = secilenTarla
    ? uygunTarlalar.find((t) => t.tarla_id === secilenTarla)?.bos_donum || 0
    : 0;

  const handleManuelChange = (e) => {
    setManuelForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const ilkPlan = sonuc?.[0];
  const urunListesi = ilkPlan?.plan || [];
  const toplamGelir = urunListesi.reduce(
    (toplam, urun) => toplam + urun.estimated_revenue,
    0
  );

  const ekimiOnayla = async () => {
    if (!ilkPlan || !ilkPlan.success || urunListesi.length === 0) return;

    setOnaylaniyor(true);
    setHata("");
    setBasariMesaji("");

    try {
      const res = await fetch("http://localhost:8000/oneri/onayla", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kullanici_id: aktifKullanici.id,
          tarla_id: secilenTarla,
          hesaplanan_toplam_kar: Math.round(toplamGelir),
          urunler: urunListesi.map((o) => ({
            urun_adi: o.product_name,
            donum: o.recommended_area,
          })),
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setBasariMesaji("✅ Ekim planı başarıyla onaylandı. Tarlanız güncellendi.");
        // Tarla listesini tazele (boş dönüm güncellensin)
        fetch(`http://localhost:8000/tarla/liste?kullanici_id=${aktifKullanici.id}`)
          .then((r) => r.json())
          .then((d) => setTarlalar(Array.isArray(d) ? d : []));
        setTimeout(() => {
            setSonuc(null);
            setBasariMesaji("");
            }, 5000);
      } else {
        const mesaj =
          typeof data.detail === "string" ? data.detail : "Onaylanamadı.";
        setHata(mesaj);
      }
    } catch (err) {
      setHata("Sunucuya bağlanılamadı.");
    } finally {
      setOnaylaniyor(false);
    }
  };

  const oneriAl = async () => {
    setHata("");

    if (!sezon) {
      setHata("Lütfen Sezon Seçiniz!");
      return;
    }

    let endpoint = "";
    let payload = {
      mod,
      sezon,
      secilen_urunler: secilenUrunler.length > 0 ? secilenUrunler : null,
      kullanici_id: aktifKullanici ? aktifKullanici.id : null,
    };

    if (mod === "tarlalarim") {
      if (!secilenTarla) {
        setHata("Lütfen bir tarla seç.");
        return;
      }
      endpoint = "http://localhost:8000/oneri/tarla_getir";

      payload = {
        kullanici_id: aktifKullanici.id,
        tarla_id: secilenTarla,
        sezon,
        bos_donum: toplamDonum,
        secilen_urunler: secilenUrunler.length > 0 ? secilenUrunler : null,
      };
    } else {
      if (!manuelForm.ilce || !manuelForm.donum) {
        setHata("Lütfen ilçe ve dönüm gir.");
        return;
      }
      endpoint = "http://localhost:8000/oneri/manual";

      payload = {
        ilce_adi: manuelForm.ilce,
        donum: Number(manuelForm.donum),
        sezon,
        secilen_urunler: secilenUrunler.length > 0 ? secilenUrunler : null,
      };
    }

    setYukleniyor(true);
    setSonuc(null);
    try {
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok) {
        setSonuc(data);
      } else {
        const mesaj =
          typeof data.detail === "string" ? data.detail : "Öneri alınamadı";
        setHata(mesaj);
      }
    } catch (err) {
      setHata("Sunucuya bağlanılamadı.");
    } finally {
      setYukleniyor(false);
    }
  };

  return (
    <div className="page-container">
      <div className="analysis-header">
        <span className="eyebrow">Öneri Sistemi</span>
        <h2>Ekim Planı Önerisi</h2>
      </div>

      <div className="analysis-grid">
        <div className="panel">
          <h3>Kaynak Seç</h3>

          <div className="source-toggle">
            <button
              type="button"
              className={mod === "tarlalarim" ? "active" : ""}
              onClick={() => setMod("tarlalarim")}
            >
              Tarlalarımdan Seç
            </button>
            <button
              type="button"
              className={mod === "manuel" ? "active" : ""}
              onClick={() => setMod("manuel")}
            >
              Kendim Girmek İstiyorum
            </button>
          </div>

          {mod === "tarlalarim" ? (
            !aktifKullanici ? (
              <div className="empty-state">
                Kayıtlı tarlalarını kullanabilmek için önce giriş yapmalısın.
              </div>
            ) : uygunTarlalar.length === 0 ? (
              <div className="empty-state">Boş dönümü olan bir tarlan yok. "Tarlalarım" sayfasından tarladüzenleyebilirsin. </div>
            ) : (
              <>
                <div className="tarla-picklist">
                  {uygunTarlalar.map((t) => (
                    <label className="tarla-pick-item" key={t.tarla_id}>
                      <input
                        type="radio"
                        name="tarla-secimi"
                        checked={secilenTarla === t.tarla_id}
                        onChange={() => tarlaSec(t.tarla_id)}
                      />
                      <div className="info">
                        <strong>{t.tarla_adi}</strong>
                        <span>{t.ilce_adi} · {t.bos_donum} dönüm boş</span>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="toplam-donum-box">Seçilen Tarlanın Boş Dönümü: {toplamDonum || 0}</div>
              </>
            )
          ) : (
            <>
              <div className="field">
                <label>İlçe</label>
                <select name="ilce"
                  value={manuelForm.ilce}
                  onChange={handleManuelChange}
                >
                  <option value="">İlçe seç</option>
                  {ILCELER.map((i) => (
                    <option key={i} value={i}>{i}</option>
                  ))}
                </select>
              </div>
              <div className="field">
                <label>Dönüm</label>
                <input
                  type="number"
                  min="0"
                  step="0.1"
                  name="donum"
                  placeholder="Örn. 10"
                  value={manuelForm.donum}
                  onChange={handleManuelChange}
                >
                </input>
              </div>
            </>
          )}

          <div className="field">
            <label>Sezon</label>
            <select value={sezon} onChange={(e) => setSezon(e.target.value)}>
              <option value="">Sezon Seç</option>
              {SEZONLAR.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
          </div>

<div className="field">
  <label>Ürün Seç</label>

  <select
    value=""
    onChange={(e) => {
      const urun = e.target.value;

      if (!urun) return;

      setSecilenUrunler((prev) =>
        prev.includes(urun) ? prev : [...prev, urun]
      );
    }}
  >
    <option value="">Ürün Seç</option>
    {urunler.map((u) => (
      <option key={u} value={u}>
        {URUN_GORUNEN_ADLAR[u]}
      </option>
    ))}
  </select>

  {secilenUrunler.length > 0 && (
    <div className="selected-products-box">
      <div className="selected-products-title">Seçilen Ürünler</div>

      <div className="selected-products-list">
        {secilenUrunler.map((u) => (
          <button
            type="button"
            key={u}
            className="selected-product-pill"
            onClick={() => urunSecimiDegistir(u)}
          >
            {URUN_GORUNEN_ADLAR[u]} ×
          </button>
        ))}
      </div>
    </div>
  )}
</div>

          {hata && <div className="form-message error">{hata}</div>}

          <button className="run-btn" onClick={oneriAl} disabled={yukleniyor}>
            {yukleniyor ? "Hesaplanıyor..." : "Öneri Al"}
          </button>
        </div>

        <div className="results-column">
            {basariMesaji && (
                <div className="form-message succes">
                    {basariMesaji}
                </div>
                )}
          {sonuc ? (
            <>
              {ilkPlan && !ilkPlan.success && (
                <div className="form-message error">{ilkPlan.error}</div>
              )}
              <div className="oneri-grid">{urunListesi.map((o, idx) => (
                  <div className="oneri-cell" key={idx}>
                    <div className="donum">{o.recommended_area} dönüm</div>
                    <div className="urun">{URUN_GORUNEN_ADLAR[o.product_name] || o.product_name}</div>
                    <div className="Meta">Tahmini Üretim:{" "}{(o.estimated_production ?? 0).toLocaleString("tr-TR")}{" "}ton</div>
                    <div className="Meta">Tarhini Gelir:{" "}{(o.estimated_revenue ?? 0).toLocaleString("tr-TR")} ₺</div>
                    <div className="Meta">Tahmini Kâr:{" "}{(o.estimated_profit ?? 0).toLocaleString("tr-TR")} ₺</div>
                  </div>
                ))}
              </div>
              <div className="result-row">
                <div className="result-card highlight">
                  <div className="label">Tahmini Toplam Gelir</div>
                  <div className="value">{toplamGelir.toLocaleString("tr-TR")} ₺</div>
                </div>
              </div>

              {basariMesaji && (
                <div className="form-message success">{basariMesaji}</div>
              )}

              {mod === "tarlalarim" && ilkPlan?.success && (
                <button
                  className="run-btn"
                  onClick={ekimiOnayla}
                  disabled={onaylaniyor}
                  style={{ marginTop: 12 }}
                >
                  {onaylaniyor ? "Kaydediliyor..." : "Bu Ekimi Onaylıyorum"}
                </button>
              )}
            </>
          ) : (
            <div className="panel">
              <div className="empty-state">
                  {basariMesaji
                    ? "✔ Ekim planı kaydedildi. Yeni bir öneri oluşturmak için tarla veya sezon seçebilirsiniz."
                    : 'Bir kaynak seç ve "Öneri Al" butonuna bas — tarlan için önerilen ekim dağılımı burada görünecek.'}</div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Recommendations;