import time
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000/cycle")
SYMBOL = os.getenv("SYMBOL", "AAPL")

def run_cycle():
    try:
        r = requests.get(API_URL, params={"symbol": SYMBOL}, timeout=20)
        print("Response:", r.status_code, r.json())
    except Exception as e:
        print("Error:", str(e))

if __name__ == "__main__":
    while True:
        run_cycle()
        time.sleep(60)