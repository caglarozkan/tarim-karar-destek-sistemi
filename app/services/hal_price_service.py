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
    "MARUL",
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
    return any(product in normalized_name for product in ALLOWED_PRODUCTS)


def fetch_daily_hal_prices(target_date=None):
    params = {}

    if target_date:
        params["tarih"] = target_date

    response = requests.get(
        URL,
        params=params,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
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

    prices = []

    for match in pattern.finditer(text):
        product_type = fix_encoding(match.group(1)).strip()
        product_name = fix_encoding(match.group(2)).strip()
        unit = fix_encoding(match.group(3)).strip()

        if not is_allowed_product(product_name):
            continue

        try:
            min_price = parse_price(match.group(4))
            max_price = parse_price(match.group(5))
            average_price = parse_price(match.group(6))
        except ValueError:
            continue

        prices.append({
            "type": product_type,
            "product_name": product_name,
            "unit": unit,
            "min_price": min_price,
            "max_price": max_price,
            "average_price": average_price,
        })

    return {
        "source": "İzmir Büyükşehir Belediyesi - Şeffaf İzmir",
        "date": target_date or date.today().isoformat(),
        "count": len(prices),
        "prices": prices,
    }