import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np
import time
from datetime import datetime

st.set_page_config(page_title="Autonomous AI Brain", layout="wide")

st.title("🧠 Autonomous AI Trading Brain")

# =========================
# INPUTS
# =========================

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("API Secret", type="password")

base_url = st.selectbox(
    "Environment",
    ["https://paper-api.alpaca.markets", "https://api.alpaca.markets"]
)

symbol = st.text_input("Symbol", "AAPL")

# =========================
# MEMORY (SESSION STATE)
# =========================

if "trade_log" not in st.session_state:
    st.session_state.trade_log = []

if "daily_pnl" not in st.session_state:
    st.session_state.daily_pnl = 0

if "kill_switch" not in st.session_state:
    st.session_state.kill_switch = False

# =========================
# RISK SYSTEM
# =========================

MAX_DAILY_LOSS = -100  # hard stop
RISK_PER_TRADE = 0.05

def risk_guard(pnl):
    if pnl <= MAX_DAILY_LOSS:
        st.session_state.kill_switch = True
        return False
    return True

# =========================
# AI BRAIN (MULTI SIGNAL)
# =========================

def brain(prices):
    prices = np.array(prices)

    short = np.mean(prices[-5:])
    long = np.mean(prices[-15:])
    momentum = prices[-1] - prices[-3]
    volatility = np.std(prices[-10:])

    vote = 0

    # Trend
    vote += 1 if short > long else -1

    # Momentum
    vote += 1 if momentum > 0 else -1

    # Volatility filter
    vote += -1 if volatility > np.mean(prices[-10:]) * 0.03 else 0

    if vote >= 2:
        return "BUY", vote
    elif vote <= -2:
        return "SELL", vote
    else:
        return "HOLD", vote

# =========================
# POSITION SIZING
# =========================

def size(cash, price):
    return max(int((cash * RISK_PER_TRADE) / price), 1)

# =========================
# CONNECT
# =========================

api = None

if st.button("START AUTONOMOUS BRAIN"):

    if api_key and api_secret:

        try:
            api = tradeapi.REST(
                api_key,
                api_secret,
                base_url=base_url,
                api_version="v2"
            )

            account = api.get_account()
            cash = float(account.cash)

            st.success("AI Brain ACTIVE")

            col1, col2, col3 = st.columns(3)
            col1.metric("Cash", account.cash)
            col2.metric("Status", account.status)
            col3.metric("Daily PnL", st.session_state.daily_pnl)

            # =========================
            # AUTONOMOUS LOOP (SIMULATED CYCLE)
            # =========================

            bars = api.get_bars(symbol, "1Min", limit=30)
            prices = [b.c for b in bars]

            decision, score = brain(prices)

            st.subheader("🧠 AI Decision Engine")
            st.write("Decision:", decision)
            st.write("Score:", score)

            price = prices[-1]
            qty = size(cash, price)

            st.write("Price:", price)
            st.write("Qty:", qty)

            # =========================
            # K