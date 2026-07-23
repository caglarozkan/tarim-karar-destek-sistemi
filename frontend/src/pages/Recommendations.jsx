import { useEffect, useState } from "react";
import "../App.css";
import { URUNLER, URUN_GORUNEN_ADLAR } from "../constants/urunler";

const ILCELER = ["Bayındır","Bergama","Menderes","Tire","Torbalı","Ödemiş"];
const SEZONLAR = ["İlkbahar","Yaz","Sonbahar","Kış"];
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
  const [sezon,setSezon] = useState("");
  const [secilenUrunler,setSecilenUrunler]=useState([]);


  useEffect(() => {
    if (aktifKullanici) {
      fetch(`http://localhost:8000/tarla/liste?kullanici_id=${aktifKullanici.id}`)
        .then((res) => res.json())
        .then((data) => setTarlalar(Array.isArray(data) ? data : []))
        .catch(() => setTarlalar([]));
    }
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

  const toplamDonum = secilenTarla ? uygunTarlalar.find((t) => t.tarla_id === secilenTarla)?.bos_donum || 0: 0;

  const handleManuelChange = (e) => {
    setManuelForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const oneriAl = async () => {
    setHata("");

    if (!sezon){
        setHata("Lütfen Sezon Seçiniz!");
        return
    }

    let payload={
        mod,
        sezon,
        secilen_urunler: secilenUrunler.length > 0 ? secilenUrunler:null,
        kullanici_id: aktifKullanici ? aktifKullanici.id : null,
        };

    if (mod === "tarlalarim") {
      if (!secilenTarla) {
        setHata("Lütfen bir tarla seç.");
        return;
      }
      payload.tarla.idleri=[secilenTarla];

    } else {
      if (!manuelForm.ilce || !manuelForm.donum) {
        setHata("Lütfen ilçe ve dönüm bilgisini doldur.");
        return;
      }
      payload.ilce=manuelForm.ilce;
      payload.donum=Number(manuelForm.donum);
    }

    setYukleniyor(true);
    setSonuc(null);
    try {
      const res = await fetch("http://localhost:8000/oneri/getir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok) {
        setSonuc(data);
      } else {
          const mesaj = typeof data.detail ==="string" ? data.detail : "Öneri alınamadı";
          setHata(mesaj);
      }
    } catch (err) {import { useEffect, useState } from "react";
import "../App.css";
import { URUNLER, URUN_GORUNEN_ADLAR } from "../constants/urunler";

const ILCELER = ["Bayındır","Bergama","Menderes","Tire","Torbalı","Ödemiş"];
const SEZONLAR = ["İlkbahar","Yaz","Sonbahar","Kış"];
function Recommendations() {
  const kayit = localStorage.getItem("kullanici");
  const aktifKullanici = kayit ? JSON.parse(kayit) : null;

  const [mod, setMod] = useState(aktifKullanici ? "tarlalarim" : "manuel");
  const [tarlalar, setTarlalar] = useState([]);
  const [secilenTarla, setSecilenTarla] = useState([]);
  const [manuelForm, setManuelForm] = useState({ ilce: "", donum: "" });
  const [sonuc, setSonuc] = useState(null);
  const [yukleniyor, setYukleniyor] = useState(false);
  const [hata, setHata] = useState("");
  const [sezon,setSezon] = useState("");
  const [secilenUrunler,setSecilenUrunler]=useState([]);


  useEffect(() => {
    if (aktifKullanici) {
      fetch(`http://localhost:8000/tarla/liste?kullanici_id=${aktifKullanici.id}`)
        .then((res) => res.json())
        .then((data) => setTarlalar(Array.isArray(data) ? data : []))
        .catch(() => setTarlalar([]));
    }
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

  const toplamDonum = secilenTarla ? uygunTarlalar.find((t) => t.tarla_id === secilenTarla)?.bos_donum || 0: 0;

  const handleManuelChange = (e) => {
    setManuelForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const oneriAl = async () => {
    setHata("");

    if (!sezon){
        setHata("Lütfen Sezon Seçiniz!");
        return
    }

    let payload={
        mod,
        sezon,
        secilen_urunler: secilenUrunler.length > 0 ? secilenUrunler: NULL,
        kullanici_id: aktifKullanici ? aktifKullanici.id : NULL,
        };

    if (mod === "tarlalarim") {
      if (!secilenTarla) {
        setHata("Lütfen bir tarla seç.");
        return;
      }
      payload.tarla.idleri=[secilenTarla];

    } else {
      if (!manuelForm.ilce || !manuelForm.donum) {
        setHata("Lütfen ilçe ve dönüm bilgisini doldur.");
        return;
      }
      payload.ilce=manuelForm.ilce;
      payload.donum=Number(manuelForm.donum);
    }

    setYukleniyor(true);
    setSonuc(null);
    try {
      const res = await fetch("http://localhost:8000/oneri/getir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok) {
        setSonuc(data);
      } else {
          const mesaj = typeof data.detail ==="string" ? data.detail : "Öneri alınamadı";
          setHata(meaj);
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
              <div className="empty-state">
                Henüz kayıtlı tarlan yok. "Tarlalarım" sayfasından tarla ekleyebilirsin.
              </div>
            ) : (
              <>
                <div className="tarla-picklist">
                  {uygunTarlalar.map((t) => (
                    <label className="tarla-pick-item" key={t.tarla_id}>
                      <input
                        type="radio" //sadece 1 tane tarla seçebilsin
                        name="tarla-secimi"
                        checked={secilenTarla===t.tarla_id}
                        onChange={() => tarlaSec(t.tarla_id)}
                      />
                      <div className="info">
                        <strong>{t.tarla_adi}</strong>
                        <span>{t.ilce_adi} · {t.bos_donum} dönüm boş </span>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="toplam-donum-box">Secilen tarlanın Boş Dönümü: {toplamDonum || 0}</div>
              </>
            )
          ) : (
            <>
              <div className="field">
                <label>İlçe</label>
                <select name="ilce" value={manuelForm.ilce} onChange={handleManuelChange}>
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
                />
              </div>
            </>
          )}
          <div className="field">
              <label>Sezonz</label>
              <select value ={sezon} onChange={(e) => setSezon(e.target.value)}>
                  <option value="">Sezon Seç</option>
                  {SEZONLAR.map((s) => (
                      <option key={s} value = {s}> {s} </option>
                      ))}
              </select>
          </div>

           <div className="field">
            <label>Ekmek İstediğin Ürünler (opsiyonel — boş bırakırsan sistem tüm ürünler arasından seçer)</label>
            <div className="urun-picklist">
              {URUNLER.map((u) => (
                <label key={u} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={secilenUrunler.includes(u)}
                    onChange={() => urunSecimiDegistir(u)}
                  />
                  {u}
                </label>
              ))}
            </div>
          </div>

          {hata && <div className="form-message error">{hata}</div>}

          <button className="run-btn" onClick={oneriAl} disabled={yukleniyor}>
            {yukleniyor ? "Hesaplanıyor..." : "Öneri Al"}
          </button>
        </div>

        <div className="results-column">
          {sonuc ? (
            <>
              <div className="oneri-grid">
                {sonuc.oneriler?.map((o, idx) => (
                  <div className="oneri-cell" key={idx}>
                    <div className="donum">{o.donum} dönüm</div>
                    <div className="urun">{o.urun}</div>
                  </div>
                ))}
              </div>
              <div className="result-row">
                <div className="result-card highlight">
                  <div className="label">Tahmini Toplam Gelirr</div>
                  <div className="value">{sonuc.tahmini_kar} ₺</div>
                </div>
              </div>
            </>
          ) : (
            <div className="panel">
              <div className="empty-state">
                Bir kaynak seç ve "Öneri Al" butonuna bas — tarlan için önerilen ekim
                dağılımı burada görünecek.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Recommendations;
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
              <div className="empty-state">
                Henüz kayıtlı tarlan yok. "Tarlalarım" sayfasından tarla ekleyebilirsin.
              </div>
            ) : (
              <>
                <div className="tarla-picklist">
                  {uygunTarlalar.map((t) => (
                    <label className="tarla-pick-item" key={t.tarla_id}>
                      <input
                        type="radio" //sadece 1 tane tarla seçebilsin
                        name="tarla-secimi"
                        checked={secilenTarla===t.tarla_id}
                        onChange={() => tarlaSec(t.tarla_id)}
                      />
                      <div className="info">
                        <strong>{t.tarla_adi}</strong>
                        <span>{t.ilce_adi} · {t.bos_donum} dönüm boş </span>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="toplam-donum-box">Secilen tarlanın Boş Dönümü: {toplamDonum || 0}</div>
              </>
            )
          ) : (
            <>
              <div className="field">
                <label>İlçe</label>
                <select name="ilce" value={manuelForm.ilce} onChange={handleManuelChange}>
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
                />
              </div>
            </>
          )}
          <div className="field">
              <label>Sezonz</label>
              <select value ={sezon} onChange={(e) => setSezon(e.target.value)}>
                  <option value="">Sezon Seç</option>
                  {SEZONLAR.map((s) => (
                      <option key={s} value = {s}> {s} </option>
                      ))}
              </select>
          </div>

           <div className="field">
            <label>Ekmek İstediğin Ürünler (opsiyonel — boş bırakırsan sistem tüm ürünler arasından seçer)</label>
            <div className="urun-picklist">
              {URUNLER.map((u) => (
                <label key={u} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <input
                    type="checkbox"
                    checked={secilenUrunler.includes(u)}
                    onChange={() => urunSecimiDegistir(u)}
                  />
                  {URUN_GORUNEN_ADLAR}
                </label>
              ))}
            </div>
          </div>

          {hata && <div className="form-message error">{hata}</div>}

          <button className="run-btn" onClick={oneriAl} disabled={yukleniyor}>
            {yukleniyor ? "Hesaplanıyor..." : "Öneri Al"}
          </button>
        </div>

        <div className="results-column">
          {sonuc ? (
            <>
              <div className="oneri-grid">
                {sonuc.oneriler?.map((o, idx) => (
                  <div className="oneri-cell" key={idx}>
                    <div className="donum">{o.donum} dönüm</div>
                    <div className="urun">{URUN_GORUNEN_ADLAR[o.urun] || o.urun}</div>
                  </div>
                ))}
              </div>
              <div className="result-row">
                <div className="result-card highlight">
                  <div className="label">Tahmini Toplam Gelirr</div>
                  <div className="value">{sonuc.tahmini_kar} ₺</div>
                </div>
              </div>
            </>
          ) : (
            <div className="panel">
              <div className="empty-state">
                Bir kaynak seç ve "Öneri Al" butonuna bas — tarlan için önerilen ekim
                dağılımı burada görünecek.
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Recommendations;
