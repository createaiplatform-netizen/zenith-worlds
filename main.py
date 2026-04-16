import time
import os
import json
import numpy as np
import pandas as pd
import requests
from datetime import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# CONFIG
# =========================
SYMBOL = "XRP"
INTERVAL = 30  # seconds

MAX_TRADE_USD = 100
MAX_DAILY_LOSS = -200

LIVE_TRADING = False  # SAFE MODE

# =========================
# SYSTEM STATE
# =========================
state = {
    "pnl": 0,
    "trades": 0,
    "kill_switch": False
}

# =========================
# DATA LAYER
# =========================
def get_data():
    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/ripple/market_chart",
        params={"vs_currency": "usd", "days": 1}
    )
    data = r.json()

    df = pd.DataFrame(data["prices"], columns=["ts", "price"])
    return df

# =========================
# SIGNAL ENGINE
# =========================
model = IsolationForest(contamination=0.03)
scaler = StandardScaler()

def generate_signal(df):
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
        if last["mom"] > 0:
            return "BUY", last["price"], float(last["score"])
        else:
            return "SELL", last["price"], float(last["score"])

    return "HOLD", last["price"], float(last["score"])

# =========================
# RISK ENGINE
# =========================
def risk_check(signal, price):
    if state["kill_switch"]:
        return False, "KILL SWITCH ACTIVE"

    if state["pnl"] <= MAX_DAILY_LOSS:
        state["kill_switch"] = True
        return False, "MAX LOSS TRIGGERED"

    return True, "OK"

# =========================
# EXECUTION ENGINE
# =========================
def execute_trade(signal, price):
    qty = MAX_TRADE_USD / price

    if not LIVE_TRADING:
        return f"PAPER TRADE → {signal} | qty={round(qty,4)}"

    import alpaca_trade_api as tradeapi

    api = tradeapi.REST(
        os.getenv("ALPACA_KEY"),
        os.getenv("ALPACA_SECRET"),
        base_url=os.getenv("ALPACA_URL")
    )

    api.submit_order(
        symbol="XRPUSD",
        qty=qty,
        side=signal.lower(),
        type="market",
        time_in_force="gtc"
    )

    return "LIVE TRADE EXECUTED"

# =========================
# LOGGING
# =========================
def log_event(event):
    event["time"] = str(datetime.utcnow())

    with open("log.jsonl", "a") as f:
        f.write(json.dumps(event) + "\n")

# =========================
# ENGINE LOOP
# =========================
def run_engine():
    print("ZENITH ENGINE STARTED")

    while True:
        try:
            df = get_data()

            signal, price, score = generate_signal(df)

            allowed, reason = risk_check(signal, price)

            if allowed and signal != "HOLD":
                result = execute_trade(signal, price)
                state["trades"] += 1
            else:
                result = f"BLOCKED → {reason}"

            log_event({
                "signal": signal,
                "price": float(price),
                "score": score,
                "result": result,
                "trades": state["trades"]
            })

            print(signal, price, score, result)

            time.sleep(INTERVAL)

        except Exception as e:
            log_event({"error": str(e)})
            time.sleep(10)

# =========================
# ENTRY POINT (RENDER SAFE)
# =========================
if __name__ == "__main__":
    run_engine()