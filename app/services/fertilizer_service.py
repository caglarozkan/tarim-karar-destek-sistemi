import re
import requests
from bs4 import BeautifulSoup
from app.services.get_usd import get_usd_try

usd_try =float(get_usd_try())

def get_commodity_price(commodity):

    url = f"https://tradingeconomics.com/commodity/{commodity}"

    headers = {
        "User-Agent":
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception("Sayfa açılamadı.")

    soup = BeautifulSoup(response.text, "html.parser")

    meta = soup.find(
        "meta",
        attrs={"name": "description"}
    )

    if meta is None:
        raise Exception("Description bulunamadı.")

    description = meta.get("content", "")


    match = re.search(
        r'(\d+(?:\.\d+)?)\s*USD/T',
        description
    )

    if match:
        return float(match.group(1))*usd_try

    raise Exception("Fiyat bulunamadı.")

price = get_commodity_price("urea")
print(price) 