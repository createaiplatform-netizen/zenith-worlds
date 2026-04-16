import os
import time
import requests
from datetime import datetime

# =========================
# CONFIG
# =========================

SYMBOL = "XRP-USD"
INTERVAL = 30

MAX_TRADE_USD = 50
LIVE_TRADING = False  # KEEP FALSE UNTIL TESTED

# =========================
# STATE
# =========================

state = {
    "trades": 0,
    "last_price": None
}

# =========================
# MARKET DATA (REAL)
# =========================

def get_price():
    url = "https://api.coinbase.com/v2/prices/XRP-USD/spot"
    r = requests.get(url).json()
    return float(r["data"]["amount"])

# =========================
# STRATEGY ENGINE (REAL LOGIC BASELINE)
# =========================

def generate_signal(price):
    if state["last_price"] is None:
        return "HOLD"

    change = (price - state["last_price"]) / state["last_price"]

    if change > 0.01:
        return "BUY"
    elif change < -0.01:
        return "SELL"
    return "HOLD"

# =========================
# EXECUTION ENGINE
# =========================

def execute_trade(signal, price):
    if signal == "HOLD":
        return "NO TRADE"

    qty = MAX_TRADE_USD / price

    if not LIVE_TRADING:
        return f"PAPER TRADE: {signal} {qty:.4f} XRP @ {price}"

    # REAL TRADING (example: Coinbase Advanced Trade API placeholder)
    api_key = os.getenv("COINBASE_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    order = {
        "product_id": SYMBOL,
        "side": signal.lower(),
        "order_configuration": {
            "market_market_ioc": {
                "base_size": str(qty)
            }
        }
    }

    # NOTE: endpoint depends on Coinbase setup
    r = requests.post(
        "https://api.coinbase.com/api/v3/brokerage/orders",
        json=order,
        headers=headers
    )

    return r.text

# =========================
# LOOP
# =========================

print("ZENITH REAL TRADING ENGINE STARTED")

while True:
    try:
        price = get_price()
        signal = generate_signal(price)

        result = execute_trade(signal, price)

        state["last_price"] = price
        state["trades"] += 1

        print({
            "time": str(datetime.utcnow()),
            "price": price,
            "signal": signal,
            "result": result
        })

        time.sleep(INTERVAL)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)