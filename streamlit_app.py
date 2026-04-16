import streamlit as st
import numpy as np
import pandas as pd
import requests
import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# LIVE SETTINGS
# =========================
LIVE_TRADING = False  # KEEP FALSE (safe mode)

# =========================
# DATA
# =========================
@st.cache_data(ttl=10)
def load_data():
    url = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    r = requests.get(url, params={"vs_currency": "usd", "days": 1}).json()
    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df

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
# REGIME FILTER
# =========================
def regime(df):
    r = df["price"].pct_change()
    vol = r.rolling(10).std().iloc[-1]

    if vol > 0.03:
        return "HIGH_VOL"
    if vol < 0.01:
        return "LOW_VOL"
    return "NORMAL"

# =========================
# SIMPLE ACTION LOGIC
# =========================
def action(state, reg):
    if reg == "HIGH_VOL":
        return "BLOCKED"

    if state == "EXPANSION":
        return "BUY"

    if state == "DISTRIBUTION":
        return "SELL"

    return "HOLD"

# =========================
# APP
# =========================
st.title("ZENITH — LIVE RUN MODE")

df = load_data()

engine = Zenith()
data, state, score = engine.run(df)

price = data["price"].iloc[-1]
reg = regime(df)
act = action(state, reg)

# =========================
# DISPLAY
# =========================
st.metric("STATE", state)
st.metric("REGIME", reg)
st.metric("ACTION", act)
st.metric("PRICE", round(price, 4))
st.metric("SCORE", round(score, 4))

st.line_chart(data.set_index("time")[["price", "score"]])