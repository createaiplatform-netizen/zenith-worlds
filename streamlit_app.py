import streamlit as st
import numpy as np
import pandas as pd
import requests
import sqlite3
import alpaca_trade_api as tradeapi
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# CONFIG
# =========================
SYMBOL = "XRPUSD"
MAX_DRAWDOWN_BLOCK = 0.20
MAX_TRADES_PER_DAY = 5

# =========================
# MEMORY DB (AUDIT LAYER)
# =========================
conn = sqlite3.connect("zenith_audit.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS trades (
    ts TEXT,
    state TEXT,
    risk TEXT,
    confidence REAL,
    action TEXT,
    qty REAL
)
""")
conn.commit()

def log_trade(state, risk, conf, action, qty):
    cursor.execute("""
        INSERT INTO trades VALUES (datetime('now'),?,?,?,?,?)
    """, (state, risk, conf, action, qty))
    conn.commit()

# =========================
# DATA LAYER (RESILIENT)
# =========================
@st.cache_data(ttl=30)
def get_data():
    url = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    params = {"vs_currency": "usd", "days": 60}
    r = requests.get(url, params=params, timeout=10).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df

# =========================
# SIGNAL ENGINE (ENHANCED)
# =========================
class ZenithEngine:
    def __init__(self):
        self.model = IsolationForest(n_estimators=400, contamination=0.03)
        self.scaler = StandardScaler()

    def features(self, df):
        df = df.copy()

        df["log_return"] = np.log(df["price"]).diff()
        df["volatility"] = df["log_return"].rolling(20).std()
        df["momentum"] = df["price"].diff(5)
        df["trend"] = df["price"].rolling(40).mean()
        df["trend_dev"] = df["price"] / (df["trend"] + 1e-9)
        df["acceleration"] = df["momentum"].diff()
        df["volume_proxy"] = df["price"].diff().abs().rolling(10).mean()

        return df.dropna()

    def run(self, df):
        df = self.features(df)

        X = self.scaler.fit_transform(df[[
            "log_return",
            "volatility",
            "momentum",
            "trend_dev",
            "acceleration",
            "volume_proxy"
        ]])

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

        confidence = float(min(1.0, abs(last["score"])))
        return df, state, confidence, float(last["volatility"])

# =========================
# RISK KERNEL (INSTITUTIONAL CORE)
# =========================
def risk_kernel(conf, vol):
    risk_score = conf * (1 + vol * 15)

    if risk_score > 1.2:
        return "BLOCKED", 0.0

    if vol > 0.06:
        return "VOLATILITY_HALT", 0.0

    if conf < 0.25:
        return "NO_TRADE", 0.0

    if risk_score < 0.5:
        return "LOW", risk_score
    if risk_score < 1.0:
        return "MEDIUM", risk_score

    return "HIGH", risk_score

# =========================
# POSITION ENGINE
# =========================
def position_size(risk):
    return {
        "LOW": 1.0,
        "MEDIUM": 0.5,
        "HIGH": 0.25
    }.get(risk, 0.0)

# =========================
# BROKER (PAPER / LIVE READY)
# =========================
def broker():
    return tradeapi.REST(
        st.secrets["ALPACA_API_KEY"],
        st.secrets["ALPACA_SECRET_KEY"],
        st.secrets["BASE_URL"],
        api_version="v2"
    )

def get_position(api):
    try:
        return float(api.get_position(SYMBOL).qty)
    except:
        return 0.0

# =========================
# EXECUTION ENGINE (INSTITUTIONAL SAFE)
# =========================
def execute(state, risk, size):
    api = broker()

    qty = max(0, round(size * 10, 2))
    position = get_position(api)

    action = "HOLD"

    if risk in ["BLOCKED", "VOLATILITY_HALT", "NO_TRADE"]:
        return {"action": "BLOCKED", "reason": risk}

    if state == "EXPANSION":
        api.submit_order(SYMBOL, qty, "buy", "market", "gtc")
        action = "BUY"

    elif state == "DISTRIBUTION" and position > 0:
        api.submit_order(SYMBOL, abs(position), "sell", "market", "gtc")
        action = "SELL"

    log_trade(state, risk, size, action, qty)

    return {"action": action, "qty": qty, "status": "submitted"}

# =========================
# APP
# =========================
st.set_page_config(page_title="ZENITH INSTITUTIONAL+", layout="wide")
st.title("🏛️ ZENITH — Institutional Production Trading Stack")

df = get_data()

engine = ZenithEngine()
data, state, conf, vol = engine.run(df)

risk, risk_score = risk_kernel(conf, vol)
size = position_size(risk)

trade = execute(state, risk, size)

# =========================
# DASHBOARD
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("STATE", state)
c2.metric("RISK", risk)
c3.metric("CONFIDENCE", round(conf, 3))

st.metric("VOLATILITY", round(vol, 5))
st.metric("POSITION SIZE", size)

st.subheader("📊 MARKET + SIGNAL")
st.line_chart(data.set_index("time")[["price", "score"]])

st.subheader("⚙️ EXECUTION")
st.json(trade)

st.subheader("🧠 AUDIT TRAIL")
st.dataframe(pd.read_sql("SELECT * FROM trades ORDER BY ts DESC LIMIT 20", conn))