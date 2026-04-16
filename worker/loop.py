import time
import requests
import os

API_URL = os.getenv("API_URL")

SYMBOL = "AAPL"

while True:
    try:
        r = requests.get(API_URL, params={"symbol": SYMBOL}, timeout=20)
        print(r.json())

    except Exception as e:
        print("error:", e)

    time.sleep(60)