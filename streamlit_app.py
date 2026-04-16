import streamlit as st
import numpy as np
import pandas as pd
import requests
import datetime
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# CONFIG
# =========================
LIVE_TRADING = False   # KEEP FALSE UNTIL TESTED
MAX_DAILY_DRAWDOWN = -150
MAX_POSITION = 200

# =========================
# MEMORY (TRADE JOURNAL)
# =========================
if "trades" not in st.session_state:
    st.session_state.trades = []
if "balance" not in st.session_state:
    st.session_state.balance = 10000
if "position" not in st.session_state:
    st.session_state.position = 0

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
# REGIME FILTER
# =========================
def market_regime(df):
    ret = df["price"].pct_change()
    vol = ret.rolling(10).std().iloc[-1]

    if vol > 0.03:
        return "HIGH_VOL"
    if vol < 0.01:
        return "LOW_VOL"
    return "NORMAL"

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
# RISK ENGINE (UPGRADED)
# =========================
def risk_engine(state, regime):
    if regime == "HIGH_VOL":
        return 0, "BLOCKED: HIGH VOL"

    if state == "EXPANSION":
        return 1
    if state == "DISTRIBUTION":
        return -1
    return 0

# =========================
# POSITION MANAGEMENT
# =========================
def stop_loss(entry, price):
    return price < entry * 0.97  # -3%

def take_profit(entry, price):
    return price > entry * 1.05  # +5%

# =========================
# EXECUTION (SIM + LIVE READY)
# =========================
def execute(signal, price):
    if signal == 0:
        return "NO TRADE"

    if st.session_state.position == 0 and signal == 1:
        st.session_state.position = MAX_POSITION / price
        st.session_state.entry = price
        return "BUY EXECUTED"

    if st.session_state.position > 0:
        if stop_loss(st.session_state.entry, price):
            st.session_state.balance += st.session_state.position * price
            st.session_state.position = 0
            return "STOP LOSS EXIT"

        if take_profit(st.session_state.entry, price):
            st.session_state.balance += st.session_state.position * price
            st.session_state.position = 0
            return "TAKE PROFIT EXIT"

        if signal == -1:
            st.session_state.balance += st.session_state.position * price
            st.session_state.position = 0
            return "MANUAL EXIT"

    return "HOLD"

# =========================
# BACKTEST (SIMPLE)
# =========================
def backtest(df):
    returns = df["price"].pct_change().fillna(0)
    return {
        "volatility": float(returns.std()),
        "trend": float(returns.mean())
    }

# =========================
# APP
# =========================
st.title("ZENITH — FULL BASELINE SYSTEM")

df = load_data()

engine = Zenith()
data, state, score = engine.run(df)

price = data["price"].iloc[-1]
regime = market_regime(df)

signal = risk_engine(state, regime)
result = execute(signal, price)
metrics = backtest(df)

portfolio_value = st.session_state.balance + st.session_state.position * price

# =========================
# DISPLAY
# =========================
st.metric("STATE", state)
st.metric("REGIME", regime)
st.metric("SIGNAL", signal)
st.metric("PRICE", round(price, 4))
st.metric("PORTFOLIO", round(portfolio_value, 2))
st.metric("ACTION", result)

st.write("Backtest snapshot:", metrics)

st.line_chart(data.set_index("time")[["price", "score"]])