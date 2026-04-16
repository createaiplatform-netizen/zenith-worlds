import streamlit as st
import numpy as np
import pandas as pd
import requests
import alpaca_trade_api as tradeapi
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# =========================
# CONFIG / SAFETY
# =========================
SYMBOL = "XRPUSD"
MAX_TRADES_PER_SESSION = 3

if "trade_count" not in st.session_state:
    st.session_state.trade_count = 0

if "log" not in st.session_state:
    st.session_state.log = []

# =========================
# DATA LAYER
# =========================
@st.cache_data(ttl=30)
def get_data():
    url = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    params = {"vs_currency": "usd", "days": 30}
    r = requests.get(url, params=params, timeout=10).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "price"])
    df["time"] = pd.to_datetime(df["ts"], unit="ms")
    return df


# =========================
# SIGNAL ENGINE
# =========================
class ZenithEngine:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=300,
            contamination=0.03,
            random_state=42
        )
        self.scaler = StandardScaler()

    def features(self, df):
        df = df.copy()

        df["log_return"] = np.log(df["price"]).diff()
        df["volatility"] = df["log_return"].rolling(20).std()
        df["momentum"] = df["price"].diff(5)
        df["trend"] = df["price"].rolling(30).mean()
        df["trend_dev"] = df["price"] / (df["trend"] + 1e-9)
        df["acceleration"] = df["momentum"].diff()

        return df.dropna()

    def run(self, df):
        df = self.features(df)

        X = self.scaler.fit_transform(
            df[[
                "log_return",
                "volatility",
                "momentum",
                "trend_dev",
                "acceleration"
            ]]
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
# RISK ENGINE
# =========================
def risk_engine(conf, vol):
    risk = conf * (1 + vol * 10)

    if risk < 0.4:
        return "LOW", risk
    elif risk < 1.0:
        return "MEDIUM", risk
    return "HIGH", risk


def position_size(risk_label):
    if risk_label == "LOW":
        return 1.0
    if risk_label == "MEDIUM":
        return 0.5
    return 0.25


# =========================
# ALPACA BROKER (PAPER)
# =========================
def get_broker():
    return tradeapi.REST(
        st.secrets["ALPACA_API_KEY"],
        st.secrets["ALPACA_SECRET_KEY"],
        st.secrets["BASE_URL"],
        api_version="v2"
    )


def get_position(api):
    try:
        pos = api.get_position(SYMBOL)
        return float(pos.qty)
    except:
        return 0.0


def execute_trade(signal, size):
    api = get_broker()

    if st.session_state.trade_count >= MAX_TRADES_PER_SESSION:
        return {"status": "BLOCKED", "reason": "trade_limit_reached"}

    qty = max(1, round(size * 10, 2))

    position = get_position(api)

    # BUY LOGIC
    if signal == "EXPANSION":
        api.submit_order(
            symbol=SYMBOL,
            qty=qty,
            side="buy",
            type="market",
            time_in_force="gtc"
        )

        st.session_state.trade_count += 1

        return {
            "action": "BUY",
            "qty": qty,
            "status": "submitted"
        }

    # SELL LOGIC
    if signal == "DISTRIBUTION" and position > 0:
        api.submit_order(
            symbol=SYMBOL,
            qty=abs(position),
            side="sell",
            type="market",
            time_in_force="gtc"
        )

        st.session_state.trade_count += 1

        return {
            "action": "SELL",
            "qty": position,
            "status": "submitted"
        }

    return {"action": "HOLD", "status": "no_trade"}


# =========================
# APP
# =========================
st.set_page_config(page_title="ZENITH LIVE TRADING", layout="wide")
st.title("🏛️ ZENITH — Live Trading System (PAPER)")

df = get_data()

engine = ZenithEngine()
data, state, conf = engine.run(df)

vol = data["volatility"].iloc[-1]

risk_label, risk_value = risk_engine(conf, vol)
size = position_size(risk_label)

signal = state

trade_result = execute_trade(signal, size)

# =========================
# MEMORY
# =========================
st.session_state.log.append({
    "state": state,
    "risk": risk_label,
    "conf": conf,
    "signal": signal
})

# =========================
# DASHBOARD
# =========================
c1, c2, c3 = st.columns(3)

c1.metric("STATE", state)
c2.metric("RISK", risk_label)
c3.metric("CONFIDENCE", round(conf, 3))

st.metric("VOLATILITY", round(vol, 5))
st.metric("POSITION SIZE", size)
st.metric("TRADES THIS SESSION", st.session_state.trade_count)

st.subheader("📊 Market + Signal")
st.line_chart(data.set_index("time")[["price", "score"]])

st.subheader("🚀 EXECUTION")
st.json(trade_result)

st.subheader("🧠 SYSTEM LOG")
st.write(st.session_state.log[-20:])