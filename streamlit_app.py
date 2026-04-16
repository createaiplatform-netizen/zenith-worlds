import streamlit as st
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# DATA LOADER
# =========================
def load_data():
    url = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    params = {"vs_currency": "usd", "days": 60}
    r = requests.get(url, params=params, timeout=10).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df


# =========================
# CORE ENGINE
# =========================
class ZenithEngine:
    def __init__(self):
        self.model = IsolationForest(n_estimators=200, contamination=0.04, random_state=42)
        self.scaler = StandardScaler()

    def features(self, df):
        df = df.copy()
        df["log_return"] = np.log(df["price"]).diff()
        df["volatility"] = df["log_return"].rolling(20).std()
        df["momentum"] = df["price"].diff(5)
        df["trend"] = df["price"].rolling(30).mean()
        df["trend_dev"] = df["price"] / (df["trend"] + 1e-9)
        return df.dropna()

    def analyze(self, df):
        df = self.features(df)

        X = self.scaler.fit_transform(
            df[["log_return", "volatility", "momentum", "trend_dev"]]
        )

        self.model.fit(X)

        df["anomaly"] = self.model.predict(X)
        df["score"] = -self.model.decision_function(X)

        last = df.iloc[-1]

        if last["anomaly"] == -1:
            if last["momentum"] > 0:
                state = "EXPANSION"
            elif last["momentum"] < 0:
                state = "DISTRIBUTION"
            else:
                state = "STRUCTURAL_SHIFT"
        else:
            state = "EQUILIBRIUM"

        return df, state, float(last["score"]), float(last["volatility"])


# =========================
# RISK ENGINE
# =========================
def risk_score(score, vol):
    risk = abs(score) * (1 + vol * 10)

    if risk < 0.5:
        return "LOW"
    elif risk < 1.2:
        return "MEDIUM"
    else:
        return "HIGH"


# =========================
# ORACLE (INTERPRETER)
# =========================
def oracle(state, risk):
    if state == "EXPANSION" and risk == "LOW":
        return "TREND CONTINUATION"
    if state == "EXPANSION" and risk == "HIGH":
        return "BREAKOUT BUT OVEREXTENDED"
    if state == "DISTRIBUTION":
        return "REVERSAL RISK"
    if state == "STRUCTURAL_SHIFT":
        return "REGIME CHANGE"
    return "NO EDGE"


# =========================
# STREAMLIT APP
# =========================
st.set_page_config(page_title="ZENITH v1.2", layout="wide")
st.title("📡 ZENITH — Market Intelligence System")

df = load_data()
engine = ZenithEngine()

data, state, score, vol = engine.analyze(df)

risk = risk_score(score, vol)
signal = oracle(state, risk)

# =========================
# DASHBOARD
# =========================
col1, col2, col3 = st.columns(3)

col1.metric("STATE", state)
col2.metric("RISK", risk)
col3.metric("SIGNAL", signal)

st.metric("ANOMALY SCORE", round(score, 4))
st.metric("VOLATILITY", round(vol, 4))

st.line_chart(data.set_index("time")[["price", "score"]])

st.subheader("Latest Data")
st.dataframe(data.tail(15))