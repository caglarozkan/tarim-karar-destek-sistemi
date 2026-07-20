import re
import json
import requests
from pathlib import Path
from datetime import date
from bs4 import BeautifulSoup
from get_usd import get_usd_try

CACHE_FILE = Path("commodity_prices.json")


def load_cache():
    if CACHE_FILE.exists():
        with open(CACHE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return {}


def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as file:
        json.dump(cache, file, ensure_ascii=False, indent=4)


def fetch_commodity_price(commodity):
    usd_try = float(get_usd_try())

    url = f"https://tradingeconomics.com/commodity/{commodity}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise Exception("Sayfa açılamadı.")

    soup = BeautifulSoup(response.text, "html.parser")

    meta = soup.find("meta", attrs={"name": "description"})

    if meta is None:
        raise Exception("Description bulunamadı.")

    description = meta.get("content", "")

    match = re.search(r'(\d+(?:\.\d+)?)\s*USD/T', description)

    if match:
        usd_price = float(match.group(1))
        return usd_price * usd_try

    raise Exception("Fiyat bulunamadı.")


def get_commodity_price(commodity):
    today = date.today().isoformat()

    cache = load_cache()

    if commodity in cache and cache[commodity]["date"] == today:
        return cache[commodity]["price"]

    price = fetch_commodity_price(commodity)

    cache[commodity] = {
        "date": today,
        "price": price
    }

    save_cache(cache)

    return price


price = get_commodity_price("urea")
print(price)