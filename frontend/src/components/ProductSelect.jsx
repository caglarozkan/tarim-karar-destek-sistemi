import Select from "react-select";
import { URUNLER, URUN_GORUNEN_ADLAR } from "../constants/urunler";
import { PRODUCT_IMAGES } from "../constants/productImages";

function ProductSelect({ value, onChange }) {
  const options = URUNLER.map((urun) => ({
    value: urun,
    label: URUN_GORUNEN_ADLAR[urun],
    image: PRODUCT_IMAGES[urun],
  }));

  return (
    <Select
      options={options}
      placeholder="Ürün seç..."
      value={options.find((o) => o.value === value)}
      onChange={(selected) => onChange(selected.value)}
      formatOptionLabel={(option) => (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <img
            src={option.image}
            alt={option.label}
            style={{
              width: 32,
              height: 32,
              objectFit: "contain",
            }}
          />

          <span>{option.label}</span>
        </div>
      )}
    />
  );
}

export default ProductSelect;