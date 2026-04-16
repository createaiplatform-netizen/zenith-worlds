import streamlit as st
import numpy as np
import pandas as pd
import requests
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Zenith v1 - Market Regime Monitor", layout="wide")

WEBHOOK_URL = st.secrets.get("WEBHOOK_URL", "") if hasattr(st, "secrets") else ""

# =========================
# DATA
# =========================
def fetch_data(days=90):
    url = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    params = {"vs_currency": "usd", "days": days}

    r = requests.get(url, params=params, timeout=10).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df

# =========================
# FEATURE ENGINE
# =========================
def build_features(df):
    df = df.copy()

    df["log_return"] = np.log(df["price"]).diff()
    df["volatility"] = df["log_return"].rolling(20).std()
    df["momentum"] = df["price"].diff(5)

    # calibration feature (prevents overreaction)
    df["volatility_regime"] = df["volatility"].rolling(50).mean()

    df = df.dropna()
    return df

# =========================
# MODEL (REGIME DETECTOR)
# =========================
class ZenithModel:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=200,
            contamination=0.05,
            random_state=42
        )

    def run(self, df):
        df = build_features(df)

        features = df[["log_return", "volatility", "momentum"]]

        X = self.scaler.fit_transform(features)
        self.model.fit(X)

        df["anomaly"] = self.model.predict(X)
        df["score"] = -self.model.decision_function(X)

        latest = df.iloc[-1]

        # =========================
        # REGIME LOGIC (CALIBRATED)
        # =========================
        vol_ratio = latest["volatility"] / (latest["volatility_regime"] + 1e-9)

        if latest["anomaly"] == -1:
            if latest["momentum"] > 0 and vol_ratio > 1.1:
                state = "🚀 EXPANSION"
            elif latest["momentum"] < 0:
                state = "⚠️ DISTRIBUTION"
            else:
                state = "⚖️ STRUCTURAL SHIFT"
        else:
            state = "🟢 EQUILIBRIUM"

        risk_score = float(latest["score"]) * float(vol_ratio)

        return df, state, risk_score

# =========================
# ALERT SYSTEM (OPTIONAL)
# =========================
def send_alert(state, price, score):
    if not WEBHOOK_URL:
        return

    try:
        requests.post(WEBHOOK_URL, json={
            "content": f"""
📡 Zenith Alert

State: {state}
Price: ${price:.4f}
Risk Score: {score:.3f}
"""
        }, timeout=5)
    except:
        pass

# =========================
# APP
# =========================
st.title("🧭 Zenith v1 — Market Regime Monitor")

model = ZenithModel()

df = fetch_data(90)
data, state, risk = model.run(df)

latest_price = df["price"].iloc[-1]

col1, col2, col3 = st.columns(3)

col1.metric("Price", f"${latest_price:.4f}")
col2.metric("Regime", state)
col3.metric("Risk Score", f"{risk:.3f}")

st.line_chart(data.set_index("time")[["price", "score"]])

st.subheader("System View")
st.write(data.tail(10))