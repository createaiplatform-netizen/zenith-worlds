import streamlit as st
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

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
# LIQUIDITY CHECK (NO EXTRA FILES)
# =========================
def liquidity_state(df):
    df = df.copy()
    df["ret"] = df["price"].pct_change()
    vol = df["ret"].rolling(10).std().iloc[-1]

    if vol > 0.03:
        return "🔴 LIQUIDITY CONTRACTING", vol
    elif vol < 0.01:
        return "🟢 LIQUIDITY EXPANDING", vol
    else:
        return "🟡 NEUTRAL", vol

# =========================
# ZENITH ENGINE
# =========================
class Zenith:
    def __init__(self):
        self.model = IsolationForest(contamination=0.03, n_estimators=200)
        self.scaler = StandardScaler()

    def run(self, df):
        df = df.copy()

        df["log_ret"] = np.log(df["price"]).diff()
        df["vol"] = df["log_ret"].rolling(20).std()
        df["mom"] = df["price"].diff(5)

        df = df.dropna()

        X = self.scaler.fit_transform(df[["log_ret", "vol", "mom"]])
        self.model.fit(X)

        df["anomaly"] = self.model.predict(X)
        df["score"] = -self.model.decision_function(X)

        last = df.iloc[-1]

        if last["anomaly"] == -1:
            state = "🚀 EXPANSION" if last["mom"] > 0 else "⚠️ DISTRIBUTION"
        else:
            state = "⚖️ EQUILIBRIUM"

        return df, state, float(last["score"])

# =========================
# APP
# =========================
st.title("ZENITH — LIVE SYSTEM (SIMPLE VERSION)")

df = load_data()

liq_state, vol = liquidity_state(df)

engine = Zenith()
data, state, score = engine.run(df)

# SIMPLE RULE LINK
if "LIQUIDITY CONTRACTING" in liq_state:
    state = "⚠️ DISTRIBUTION (LIQUIDITY RISK)"

# =========================
# DISPLAY
# =========================
st.metric("ZENITH STATE", state)
st.metric("LIQUIDITY", liq_state)
st.metric("ANOMALY SCORE", round(score, 4))
st.metric("VOLATILITY", round(vol, 5))

st.line_chart(data.set_index("time")[["price", "score"]])