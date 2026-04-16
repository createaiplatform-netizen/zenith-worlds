import time
import os
import json
import numpy as np
import pandas as pd
import requests
from datetime import datetime
from flask import Flask, jsonify
from threading import Thread
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# CONFIG
# =========================
SYMBOL = "XRPUSD"
INTERVAL = 30
MAX_TRADE_USD = 50
MAX_DAILY_LOSS = -200

LIVE_TRADING = False  # 🚨 KEEP FALSE UNTIL TESTED

state = {
    "pnl": 0,
    "trades_today": 0,
    "kill_switch": False
}

# =========================
# BROKER (ALPACA)
# =========================
if LIVE_TRADING:
    import alpaca_trade_api as tradeapi

    api = tradeapi.REST(
        os.getenv("ALPACA_KEY"),
        os.getenv("ALPACA_SECRET"),
        base_url=os.getenv("ALPACA_URL")
    )

# =========================
# SIGNAL ENGINE
# =========================
model = IsolationForest(contamination=0.03)
scaler = StandardScaler()

def get_data():
    r = requests.get(
        "https://api.coingecko.com/api/v3/coins/ripple/market_chart",
        params={"vs_currency": "usd", "days": 1}
    ).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    return df

def generate_signal(df):
    df["ret"] = np.log(df["price"]).diff()
    df["vol"] = df["ret"].rolling(20).std()
    df["mom"] = df["price"].diff(5)
    df = df.dropna()

    X = scaler.fit_transform(df[["ret","vol","mom"]])
    model.fit(X)

    df["anomaly"] = model.predict(X)
    df["score"] = -model.decision_function(X)

    last = df.iloc[-1]

    if last["anomaly"] == -1:
        return ("BUY" if last["mom"] > 0 else "SELL"), last["price"], float(last["score"])

    return "HOLD", last["price"], float(last["score"])

# =========================
# RISK GOVERNOR
# =========================
def risk_check(signal, price):
    if state["kill_switch"]:
        return False, "KILL SWITCH ACTIVE"

    if state["pnl"] <= MAX_DAILY_LOSS:
        state["kill_switch"] = True
        return False, "MAX LOSS HIT"

    if state["trades_today"] > 20:
        return False, "TRADE LIMIT"

    return True, "OK"

# =========================
# EXECUTION
# =========================
def execute(signal, price):
    qty = MAX_TRADE_USD / price

    if not LIVE_TRADING:
        return f"PAPER {signal} {round(qty,4)}"

    try:
        order = api.submit_order(
            symbol=SYMBOL,
            qty=qty,
            side=signal.lower(),
            type="market",
            time_in_force="gtc"
        )
        return "LIVE EXECUTED"
    except Exception as e:
        return str(e)

# =========================
# LOGGING
# =========================
def log(entry):
    entry["time"] = str(datetime.utcnow())

    with open("log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

# =========================
# ENGINE LOOP
# =========================
def run_engine():
    print("ZENITH ENGINE RUNNING")

    while True:
        try:
            df = get_data()
            signal, price, score = generate_signal(df)

            allowed, reason = risk_check(signal, price)

            if allowed and signal != "HOLD":
                result = execute(signal, price)
                state["trades_today"] += 1
            else:
                result = f"BLOCKED: {reason}"

            entry = {
                "signal": signal,
                "price": price,
                "score": score,
                "result": result
            }

            print(entry)
            log(entry)

            time.sleep(INTERVAL)

        except Exception as e:
            log({"error": str(e)})
            time.sleep(10)

# =========================
# CONTROL API
# =========================
app = Flask(__name__)

@app.route("/")
def status():
    return jsonify({
        "status": "running",
        "state": state
    })

@app.route("/kill")
def kill():
    state["kill_switch"] = True
    return jsonify({"status": "KILLED"})

@app.route("/resume")
def resume():
    state["kill_switch"] = False
    return jsonify({"status": "RESUMED"})

# =========================
# START BOTH SYSTEMS
# =========================
if __name__ == "__main__":
    Thread(target=run_engine).start()
    app.run(host="0.0.0.0", port=10000)