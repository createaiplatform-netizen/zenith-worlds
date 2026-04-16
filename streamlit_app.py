import time
import numpy as np
import pandas as pd
import requests
import os
import json
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import alpaca_trade_api as tradeapi

# =========================
# CONFIG
# =========================
SYMBOL = "XRPUSD"
INTERVAL = 30
MAX_POSITION_USD = 200
MAX_DAILY_LOSS = -150
KILL_SWITCH = False

# =========================
# BROKER
# =========================
api = tradeapi.REST(
    os.getenv("ALPACA_KEY"),
    os.getenv("ALPACA_SECRET"),
    base_url=os.getenv("BASE_URL")
)

# =========================
# STATE
# =========================
state = {
    "pnl": 0,
    "position": 0,
    "entry": 0,
    "trades": []
}

# =========================
# DATA
# =========================
def get_data():
    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/ripple/market_chart",
        params={"vs_currency": "usd", "days": 1}
    ).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df

# =========================
# SIGNAL ENGINE
# =========================
model = IsolationForest(contamination=0.03)
scaler = StandardScaler()

def signal_engine(df):
    df = df.copy()

    df["ret"] = np.log(df["price"]).diff()
    df["vol"] = df["ret"].rolling(20).std()
    df["mom"] = df["price"].diff(5)
    df = df.dropna()

    X = scaler.fit_transform(df[["ret", "vol", "mom"]])
    model.fit(X)

    df["anomaly"] = model.predict(X)
    df["score"] = -model.decision_function(X)

    last = df.iloc[-1]

    if last["anomaly"] == -1:
        return ("BUY" if last["mom"] > 0 else "SELL"), last["price"], float(last["score"])

    return "HOLD", last["price"], float(last["score"])

# =========================
# RISK ENGINE (SURVIVAL LAYER)
# =========================
def risk_check(signal, price):
    global KILL_SWITCH

    if KILL_SWITCH:
        return False, "KILL SWITCH ACTIVE"

    if state["pnl"] <= MAX_DAILY_LOSS:
        KILL_SWITCH = True
        return False, "MAX LOSS REACHED"

    if price <= 0:
        return False, "BAD DATA"

    return True, "OK"

# =========================
# POSITION SIZING
# =========================
def size_position(price):
    return MAX_POSITION_USD / price

# =========================
# EXECUTION
# =========================
def execute(signal, price):
    qty = size_position(price)

    try:
        order = api.submit_order(
            symbol=SYMBOL,
            qty=qty,
            side=signal.lower(),
            type="market",
            time_in_force="gtc"
        )

        return f"EXECUTED {signal} {qty}"

    except Exception as e:
        return f"FAILED {str(e)}"

# =========================
# MEMORY (THE SYSTEM LEARNS HISTORY ONLY)
# =========================
def log(entry):
    entry["time"] = str(datetime.utcnow())
    state["trades"].append(entry)

    with open("journal.log", "a") as f:
        f.write(json.dumps(entry) + "\n")

# =========================
# MAIN LOOP (AUTONOMOUS)
# =========================
while True:
    try:
        df = get_data()

        signal, price, score = signal_engine(df)

        allowed, reason = risk_check(signal, price)

        if allowed and signal != "HOLD":
            result = execute(signal, price)
        else:
            result = f"BLOCKED: {reason}"

        log({
            "signal": signal,
            "price": price,
            "score": score,
            "result": result
        })

        time.sleep(INTERVAL)

    except Exception as e:
        log({"error": str(e)})
        time.sleep(10)