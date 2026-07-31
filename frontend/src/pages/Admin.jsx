import React, { useEffect, useState } from "react";

const API_URL = "http://127.0.0.1:8000";

function Admin() {
  const [kullanicilar, setKullanicilar] = useState([]);
  const [urunler, setUrunler] = useState([]);

  const [yukleniyor, setYukleniyor] = useState(true);
  const [hata, setHata] = useState("");

  const kayit = localStorage.getItem("kullanici");
  const aktifKullanici = kayit ? JSON.parse(kayit) : null;
  const adminId = aktifKullanici ? aktifKullanici.id : null;

  useEffect(() => {
    if (!adminId) {
      setHata("Kullanıcı bilgisi bulunamadı.");
      setYukleniyor(false);
      return;
    }

    verileriGetir();
  }, []);

  const verileriGetir = async () => {
    try {
      setYukleniyor(true);
      setHata("");

      const [kullaniciResponse, urunResponse] = await Promise.all([
        fetch(`${API_URL}/admin/kullanicilar?admin_id=${adminId}`),
        fetch(`${API_URL}/admin/urunler?admin_id=${adminId}`),
      ]);

      if (!kullaniciResponse.ok) {
        const data = await kullaniciResponse.json();

        if (kullaniciResponse.status === 403) {
          throw new Error("Bu işlem için admin yetkiniz bulunmuyor.");
        }

        throw new Error(
          data.detail || "Kullanıcılar alınamadı."
        );
      }

      if (!urunResponse.ok) {
        const data = await urunResponse.json();

        if (urunResponse.status === 403) {
          throw new Error("Bu işlem için admin yetkiniz bulunmuyor.");
        }

        throw new Error(
          data.detail || "Ürünler alınamadı."
        );
      }

      const kullaniciData = await kullaniciResponse.json();
      const urunData = await urunResponse.json();

      setKullanicilar(kullaniciData);
      setUrunler(urunData);

    } catch (error) {
      console.error("Admin paneli hatası:", error);
      setHata(error.message);
    } finally {
      setYukleniyor(false);
    }
  };

  // Kullanıcıyı admin yap / adminliğini kaldır
  const adminYetkisiniDegistir = async (kullaniciId) => {
    try {
      const response = await fetch(
        `${API_URL}/admin/kullanicilar/${kullaniciId}/admin?admin_id=${adminId}`,
        {
          method: "PUT",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Admin yetkisi değiştirilemedi."
        );
      }

      setKullanicilar((oncekiKullanicilar) =>
        oncekiKullanicilar.map((kullanici) =>
          kullanici.kullanici_id === kullaniciId
            ? {
                ...kullanici,
                is_admin: data.is_admin,
              }
            : kullanici
        )
      );

    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  };

  // Ürünü aktif / pasif yap
  const urunDurumunuDegistir = async (urunId) => {
    try {
      const response = await fetch(
        `${API_URL}/admin/urunler/${urunId}/adurum?admin_id=${adminId}`,
        {
          method: "PUT",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Ürün durumu değiştirilemedi."
        );
      }

      setUrunler((oncekiUrunler) =>
        oncekiUrunler.map((urun) =>
          urun.urun_id === urunId
            ? {
                ...urun,
                aktif: data.aktif,
              }
            : urun
        )
      );

    } catch (error) {
      console.error(error);
      alert(error.message);
    }
  };

  if (yukleniyor) {
    return (
      <div className="admin-container">
        <div className="admin-loading">
          Admin paneli yükleniyor...
        </div>
      </div>
    );
  }

  if (hata) {
    return (
      <div className="admin-container">
        <div className="admin-error">
          <h2>Erişim Hatası</h2>

          <p>{hata}</p>

          <button onClick={verileriGetir}>
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <div>
          <h1>Admin Paneli</h1>

          <p>
            Kullanıcı ve ürün yönetimini buradan
            gerçekleştirebilirsiniz.
          </p>
        </div>
      </div>

      <div className="admin-stats">

        <div className="admin-stat-card">
          <div className="admin-stat-title">
            Toplam Kullanıcı
          </div>

          <div className="admin-stat-number">
            {kullanicilar.length}
          </div>
        </div>

        <div className="admin-stat-card">
          <div className="admin-stat-title">
            Toplam Ürün
          </div>

          <div className="admin-stat-number">
            {urunler.length}
          </div>
        </div>
        <div className="admin-stat-card">
          <div className="admin-stat-title">
            Aktif Ürün
          </div>

          <div className="admin-stat-number">
            {urunler.filter((urun) => urun.aktif).length}
          </div>
        </div>
        <div className="admin-stat-card">
          <div className="admin-stat-title">
            Pasif Ürün
          </div>

          <div className="admin-stat-number">
            {urunler.filter((urun) => !urun.aktif).length}
          </div>
        </div>
      </div>
      <section className="admin-section">
        <div className="admin-section-header">
          <div>
            <h2>Kullanıcı Yönetimi</h2>
            <p>
              Sistemde kayıtlı kullanıcıları yönetin.
            </p>
          </div>
        </div>
        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Ad Soyad</th>
                <th>Email</th>
                <th>Telefon</th>
                <th>Rol</th>
                <th>İşlem</th>
              </tr>
            </thead>
            <tbody>
              {kullanicilar.length === 0 ? (
                <tr>
                  <td
                    colSpan="6"
                    className="empty-message"
                  >
                    Kayıtlı kullanıcı bulunamadı.
                  </td>
                </tr>
              ) : (
                kullanicilar.map((kullanici) => (
                  <tr key={kullanici.kullanici_id}>
                    <td>
                      {kullanici.kullanici_id}
                    </td>
                    <td>
                      {kullanici.ad_soyad}
                    </td>
                    <td>
                      {kullanici.email}
                    </td>
                    <td>
                      {kullanici.telefon || "-"}
                    </td>
                    <td>
                      <span
                        className={
                          kullanici.is_admin
                            ? "role-badge admin-role"
                            : "role-badge user-role"
                        }
                      >
                        {kullanici.is_admin
                          ? "Admin"
                          : "Kullanıcı"}
                      </span>
                    </td>
                    <td>
                      {kullanici.kullanici_id ===
                      Number(adminId) ? (
                        <span className="current-admin">
                          Siz
                        </span>
                      ) : (
                        <button
                          className={
                            kullanici.is_admin
                              ? "action-button remove-admin"
                              : "action-button make-admin"
                          }
                          onClick={() =>
                            adminYetkisiniDegistir(
                              kullanici.kullanici_id
                            )
                          }
                        >
                          {kullanici.is_admin
                            ? "Adminliği Kaldır"
                            : "Admin Yap"}
                        </button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>

      <section className="admin-section">
        <div className="admin-section-header">
          <div>
            <h2>Ürün Yönetimi</h2>
            <p>
              Kullanıcıların seçim yapabileceği
              ürünleri yönetin.
            </p>
          </div>
        </div>
        <div className="admin-table-wrapper">
          <table className="admin-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Ürün Adı</th>
                <th>Durum</th>
                <th>İşlem</th>
              </tr>
            </thead>
            <tbody>
              {urunler.length === 0 ? (
                <tr>
                  <td
                    colSpan="4"
                    className="empty-message"
                  >
                    Ürün bulunamadı.
                  </td>
                </tr>
              ) : (
                urunler.map((urun) => (
                  <tr key={urun.urun_id}>
                    <td>
                      {urun.urun_id}
                    </td>
                    <td className="product-name">
                      {urun.urun_adi}
                    </td>
                    <td>
                      <span
                        className={
                          urun.aktif
                            ? "status-badge active-status"
                            : "status-badge passive-status"
                        }
                      >
                        {urun.aktif
                          ? "Aktif"
                          : "Pasif"}
                      </span>
                    </td>
                    <td>
                      <button
                        className={
                          urun.aktif
                            ? "action-button deactivate-product"
                            : "action-button activate-product"
                        }
                        onClick={() =>
                          urunDurumunuDegistir(
                            urun.urun_id
                          )
                        }
                      >
                        {urun.aktif
                          ? "Pasifleştir"
                          : "Aktifleştir"}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}

export default Admin;