import requests

def get_usd_try():
    url = "https://open.er-api.com/v6/latest/USD"

    response = requests.get(url)
    data = response.json()

    return data["rates"]["TRY"]
