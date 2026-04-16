import os
import time
import requests
from datetime import datetime

SYMBOL = "XRP-USD"
INTERVAL = 30

MAX_TRADE_USD = 50
LIVE_TRADING = False  # KEEP FALSE UNTIL READY

state = {"last_price": None}

def get_price():
    r = requests.get("https://api.coinbase.com/v2/prices/XRP-USD/spot")
    return float(r.json()["data"]["amount"])

def signal(price):
    if state["last_price"] is None:
        return "HOLD"

    change = (price - state["last_price"]) / state["last_price"]

    if change > 0.01:
        return "BUY"
    if change < -0.01:
        return "SELL"
    return "HOLD"

def log(msg):
    print(f"[{datetime.utcnow().isoformat()}] {msg}", flush=True)

while True:
    try:
        price = get_price()
        sig = signal(price)

        state["last_price"] = price

        log(f"{SYMBOL} PRICE={price} SIGNAL={sig}")

        time.sleep(INTERVAL)

    except Exception as e:
        log(f"ERROR: {e}")
        time.sleep(5)