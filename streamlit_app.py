import streamlit as st
import numpy as np
import pandas as pd
import requests
import time
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# DATA LAYER
# =========================
def get_data():
    url = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    params = {"vs_currency": "usd", "days": 30}
    r = requests.get(url, params=params).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df


# =========================
# SIGNAL ENGINE
# =========================
class ZenithSignal:
    def __init__(self):
        self.model = IsolationForest(n_estimators=300, contamination=0.03)
        self.scaler = StandardScaler()

    def features(self, df):
        df = df.copy()

        df["log_return"] = np.log(df["price"]).diff()
        df["volatility"] = df["log_return"].rolling(20).std()
        df["momentum"] = df["price"].diff(5)
        df["trend"] = df["price"].rolling(30).mean()
        df["trend_dev"] = df["price"] / (df["trend"] + 1e-9)

        return df.dropna()

    def run(self, df):
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
            else:
                state = "DISTRIBUTION"
        else:
            state = "EQUILIBRIUM"

        confidence = float(min(1.0, abs(last["score"])))

        return df, state, confidence


# =========================
# RISK FIREWALL (REAL INSTITUTIONAL CONCEPT)
# =========================
def risk_firewall(conf, vol, equity=1000):
    exposure = conf * equity

    max_exposure = equity * 0.25
    if exposure > max_exposure:
        return "RISK CUT", 0.0

    if vol > 0.05:
        return "VOLATILITY HALT", 0.0

    if conf < 0.2:
        return "NO TRADE", 0.0

    return "OK", exposure


# =========================
# EXECUTION ENGINE (SIMULATED)
# =========================
def execute(signal, exposure):
    return {
        "signal": signal,
        "order_type": "MARKET_SIM",
        "exposure": round(exposure, 2),
        "status": "FILLED_SIMULATION"
    }


# =========================
# STREAMLIT STATE
# =========================
st.set_page_config(page_title="ZENITH INSTITUTIONAL STACK", layout="wide")
st.title("🏛️ ZENITH — Institutional Live Trading Stack (SIMULATED)")

df = get_data()

engine = ZenithSignal()
data, state, conf = engine.run(df)

vol = data["volatility"].iloc[-1]

risk_status, exposure = risk_firewall(conf, vol)
exec_report = execute(state, exposure)

# =========================
# DASHBOARD
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("STATE", state)
c2.metric("CONFIDENCE", round(conf, 3))
c3.metric("RISK STATUS", risk_status)

st.metric("EXPOSURE", exposure)
st.metric("VOLATILITY", round(vol, 4))

st.subheader("📊 Market + Signal")
st.line_chart(data.set_index("time")[["price", "score"]])

st.subheader("⚙️ Execution Layer")
st.json(exec_report)