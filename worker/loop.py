import time
import requests

API = "http://localhost:8000/cycle"

SYMBOL = "AAPL"

while True:
    try:
        r = requests.post(API, params={"symbol": SYMBOL})
        print(r.json())
    except Exception as e:
        print("error:", e)

    time.sleep(60)