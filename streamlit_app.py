import streamlit as st
import pandas as pd
import numpy as np
import requests
import sqlite3
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from datetime import datetime

# =========================
# CONFIG
# =========================
st.set_page_config(page_title="Zenith v1.2", layout="wide")

API_URL = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"

DB_NAME = "zenith_memory.db"

DISCORD_WEBHOOK = st.secrets.get("DISCORD_WEBHOOK", None)

# =========================
# MEMORY LAYER (SQLite)
# =========================
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS signals (
            time TEXT,
            price REAL,
            state TEXT,
            score REAL
        )
    """)
    conn.commit()
    conn.close()

def log_signal(price, state, score):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute(
        "INSERT INTO signals VALUES (?, ?, ?, ?)",
        (str(datetime.utcnow()), float(price), state, float(score))
    )
    conn.commit()
    conn.close()

def load_signals():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM signals", conn)
    conn.close()
    return df

# =========================
# DATA LAYER
# =========================
@st.cache_data(ttl=60)
def load_data(days=180):
    r = requests.get(API_URL, params={"vs_currency": "usd", "days": days}, timeout=10).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df

# =========================
# FEATURES
# =========================
def features(df):
    df = df.copy()

    df["log_return"] = np.log(df["price"]).diff()
    df["volatility"] = df["log_return"].rolling(20).std()
    df["momentum"] = df["price"].diff(5)
    df["trend"] = df["price"].rolling(10).mean() - df["price"].rolling(30).mean()

    return df.dropna()

# =========================
# ORACLE ENGINE
# =========================
class ZenithEngine:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=0.04,
            random_state=42
        )
        self.scaler = StandardScaler()

        self.history = []

    def analyze(self, df):
        df = features(df)

        X = self.scaler.fit_transform(df[["log_return", "volatility", "momentum", "trend"]])
        self.model.fit(X)

        df["anomaly"] = self.model.predict(X)
        df["score"] = -self.model.decision_function(X)

        last = df.iloc[-1]

        if last["anomaly"] == -1:
            if last["momentum"] > 0:
                state = "EXPANSION"
                bias = 1
            else:
                state = "DISTRIBUTION"
                bias = -1
        else:
            state = "EQUILIBRIUM"
            bias = 0

        self.history.append(bias)
        if len(self.history) > 200:
            self.history.pop(0)

        confidence = np.mean(np.abs(self.history)) if self.history else 0

        return df, state, float(last["score"]), confidence, float(last["price"])

# =========================
# ALERT SYSTEM
# =========================
def send_alert(state, price, score):
    if not DISCORD_WEBHOOK:
        return

    if state == "EQUILIBRIUM":
        return

    payload = {
        "content": f"🧠 ZENITH ALERT\nSTATE: {state}\nPRICE: {price:.4f}\nSCORE: {score:.3f}"
    }

    try:
        requests.post(DISCORD_WEBHOOK, json=payload, timeout=5)
    except:
        pass

# =========================
# BACKTEST (SIMPLE EDGE CHECK)
# =========================
def backtest(df):
    df = features(df)

    engine = ZenithEngine()

    results = []

    for i in range(100, len(df)):
        window = df.iloc[:i]

        try:
            _, state, score, _, price = engine.analyze(window)

            future = df.iloc[i]["price"]
            forward_return = (future - price) / price

            results.append([state, score, forward_return])

        except:
            continue

    out = pd.DataFrame(results, columns=["state", "score", "return"])

    return out

# =========================
# INIT
# =========================
init_db()

engine = ZenithEngine()
df = load_data()

data, state, score, confidence, price = engine.analyze(df)

log_signal(price, state, score)
send_alert(state, price, score)

# =========================
# UI
# =========================
st.title("🧠 Zenith v1.2 — Market Sensor System")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Price", f"${price:.4f}")
c2.metric("State", state)
c3.metric("Anomaly Score", round(score, 4))
c4.metric("Confidence", round(confidence, 3))

st.divider()

st.subheader("Market Structure")
st.line_chart(data.set_index("time")[["price", "score"]])

# =========================
# MEMORY VIEW
# =========================
st.subheader("Signal Memory (SQLite)")
mem = load_signals()
st.dataframe(mem.tail(50))

# =========================
# BACKTEST PANEL
# =========================
if st.button("Run Backtest (Last 180 Days)"):
    bt = backtest(load_data(180))

    st.subheader("Backtest Results")

    st.write("Avg Return when EXPANSION:")
    st.write(bt[bt["state"] == "EXPANSION"]["return"].mean())

    st.write("Avg Return when DISTRIBUTION:")
    st.write(bt[bt["state"] == "DISTRIBUTION"]["return"].mean())

    st.line_chart(bt["return"])

st.caption(f"Zenith v1.2 | {datetime.utcnow()} UTC")