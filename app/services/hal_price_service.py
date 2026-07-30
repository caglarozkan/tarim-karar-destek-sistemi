import re
import requests
from bs4 import BeautifulSoup
from datetime import date

URL = "https://www.izmir.bel.tr/tr/SeffafIzmir/HalFiyatlari/sebze"

ALLOWED_PRODUCTS = [
    "DOMATES SALKIM",
    "BİBER SİVRİ",
    "SALATALIK SİLOR",
    "KABAK",
    "KARPUZ",
    "PATLICAN UZUN",
    "MARUL",
    "ISPANAK",
    "BROKOLI",
    "BEZELYE",
    "LAHANA BEYAZ",
    "LAHANA KIRMIZI",
    "BAKLA",
    "PIRASA",
    "KARNABAHAR",
]


def fix_encoding(value):
    value = str(value)

    if any(bad in value for bad in ["Ã", "Ä", "Å"]):
        try:
            return value.encode("latin1").decode("utf-8")
        except UnicodeError:
            return value

    return value


def normalize_text(value):
    value = fix_encoding(value).upper().strip()

    value = (
        value
        .replace("İ", "I")
        .replace("Ş", "S")
        .replace("Ğ", "G")
        .replace("Ü", "U")
        .replace("Ö", "O")
        .replace("Ç", "C")
    )

    return " ".join(value.split())


NORMALIZED_ALLOWED_PRODUCTS = [
    normalize_text(product)
    for product in ALLOWED_PRODUCTS
]


def parse_price(value):
    value = fix_encoding(value)
    value = value.replace("TL", "")
    value = value.replace("En Az:", "")
    value = value.replace("En Çok:", "")
    value = value.replace("Ortalama:", "")
    value = value.strip()
    value = value.replace(".", "").replace(",", ".")

    return float(value)


def is_allowed_product(name):
    normalized_name = normalize_text(name)

    return any(
        allowed_product in normalized_name
        for allowed_product in NORMALIZED_ALLOWED_PRODUCTS
    )


def get_display_product_name(normalized_name):
    for product in ALLOWED_PRODUCTS:
        if normalize_text(product) == normalized_name:
            return product

    return normalized_name


def fetch_daily_hal_prices(target_date=None):
    params = {}

    if target_date:
        params["tarih"] = target_date

    response = requests.get(
        URL,
        params=params,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=5,
    )
    response.raise_for_status()
    response.encoding = response.apparent_encoding or "utf-8"

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text("\n", strip=True)
    text = fix_encoding(text)

    pattern = re.compile(
        r"(SEBZE|MEYVE|İTHAL|ITHAL)\s+"
        r"(.+?)\s+"
        r"Birim:\s*(.+?)\s+"
        r"En Az:\s*([\d\.,]+)\s+"
        r"En Çok:\s*([\d\.,]+)\s+"
        r"Ortalama:\s*([\d\.,]+)",
        re.DOTALL,
    )

    found_prices = {}

    for match in pattern.finditer(text):
        product_type = fix_encoding(match.group(1)).strip()
        product_name = fix_encoding(match.group(2)).strip()
        unit = fix_encoding(match.group(3)).strip()
        normalized_product_name = normalize_text(product_name)

        if not is_allowed_product(product_name):
            continue

        try:
            min_price = parse_price(match.group(4))
            max_price = parse_price(match.group(5))
            average_price = parse_price(match.group(6))
        except ValueError:
            continue

        matched_allowed_product = None

        for allowed_product in NORMALIZED_ALLOWED_PRODUCTS:
            if allowed_product in normalized_product_name:
                matched_allowed_product = allowed_product
                break

        if matched_allowed_product is None:
            continue

        found_prices[matched_allowed_product] = {
            "type": product_type,
            "product_name": get_display_product_name(matched_allowed_product),
            "market_product_name": product_name,
            "unit": unit,
            "min_price": min_price,
            "max_price": max_price,
            "average_price": average_price,
            "price_found": True,
            "is_current": True,
            "note": "Güncel hal fiyatı",
        }

    prices = []

    for allowed_product in NORMALIZED_ALLOWED_PRODUCTS:
        if allowed_product in found_prices:
            prices.append(found_prices[allowed_product])
        else:
            prices.append({
                "type": "-",
                "product_name": get_display_product_name(allowed_product),
                "market_product_name": None,
                "unit": "-",
                "min_price": None,
                "max_price": None,
                "average_price": None,
                "price_found": False,
                "is_current": False,
                "note": "Bugünkü hal fiyatı bulunamadı.",
            })

    return {
        "source": "İzmir Büyükşehir Belediyesi - Şeffaf İzmir",
        "date": target_date or date.today().isoformat(),
        "count": len(prices),
        "prices": prices,
    }