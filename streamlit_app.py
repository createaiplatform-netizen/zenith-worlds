import streamlit as st
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import datetime

# =========================
# CONFIG (SAFE BY DEFAULT)
# =========================
MAX_TRADES_PER_DAY = 3
TRADE_ENABLED = False  # <- TURN TO True ONLY WHEN READY

# =========================
# DATA
# =========================
@st.cache_data(ttl=30)
def load_data():
    url = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    params = {"vs_currency": "usd", "days": 30}
    r = requests.get(url, params=params).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df

# =========================
# LIQUIDITY MODULE
# =========================
def liquidity(df):
    df = df.copy()
    df["ret"] = df["price"].pct_change()
    vol = df["ret"].rolling(10).std().iloc[-1]

    if vol > 0.03:
        return "🔴 CONTRACTING", vol
    elif vol < 0.01:
        return "🟢 EXPANDING", vol
    return "🟡 NEUTRAL", vol

# =========================
# ZENITH ENGINE
# =========================
class Zenith:
    def __init__(self):
        self.model = IsolationForest(contamination=0.03)
        self.scaler = StandardScaler()

    def run(self, df):
        df = df.copy()

        df["ret"] = np.log(df["price"]).diff()
        df["vol"] = df["ret"].rolling(20).std()
        df["mom"] = df["price"].diff(5)

        df = df.dropna()

        X = self.scaler.fit_transform(df[["ret", "vol", "mom"]])
        self.model.fit(X)

        df["anomaly"] = self.model.predict(X)
        df["score"] = -self.model.decision_function(X)

        last = df.iloc[-1]

        if last["anomaly"] == -1:
            state = "EXPANSION" if last["mom"] > 0 else "DISTRIBUTION"
        else:
            state = "EQUILIBRIUM"

        return df, state, float(last["score"])

# =========================
# RISK ENGINE
# =========================
def risk_manager(state, liq):
    if liq == "🔴 CONTRACTING":
        return 0.0, "BLOCKED (LIQUIDITY)"

    if state == "EXPANSION":
        return 0.5, "BUY SIGNAL"
    elif state == "DISTRIBUTION":
        return -0.5, "SELL SIGNAL"

    return 0.0, "NO TRADE"

# =========================
# PAPER EXECUTION (SAFE MOCK)
# =========================
trade_log = []

def execute(signal_size, signal):
    if not TRADE_ENABLED:
        return "PAPER MODE: NO REAL TRADE EXECUTED"

    if signal_size == 0:
        return "NO TRADE"

    return f"EXECUTED {signal} SIZE {signal_size}"

# =========================
# APP
# =========================
st.title("🏛️ ZENITH AUTO TRADER (SAFE MODE)")

df = load_data()

liq_state, vol = liquidity(df)

engine = Zenith()
data, state, score = engine.run(df)

size, signal = risk_manager(state, liq_state)

result = execute(size, signal)

# =========================
# DISPLAY
# =========================
st.metric("STATE", state)
st.metric("LIQUIDITY", liq_state)
st.metric("RISK SIGNAL", signal)
st.metric("ANOMALY SCORE", round(score, 4))
st.metric("TRADE RESULT", result)

st.line_chart(data.set_index("time")[["price", "score"]])