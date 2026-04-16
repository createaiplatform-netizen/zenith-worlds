import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np
import time
from datetime import datetime

st.title("🧠 100% AI Trading Brain System")

# =========================
# INPUTS
# =========================

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("API Secret", type="password")

symbol = st.text_input("Symbol", "AAPL")

base_url = "https://paper-api.alpaca.markets"

# =========================
# MEMORY
# =========================

if "log" not in st.session_state:
    st.session_state.log = []

if "running" not in st.session_state:
    st.session_state.running = False

# =========================
# AI BRAIN
# =========================

def brain(prices):
    prices = np.array(prices)

    short = np.mean(prices[-5:])
    long = np.mean(prices[-20:])
    momentum = prices[-1] - prices[-3]

    score = 0

    score += 1 if short > long else -1
    score += 1 if momentum > 0 else -1

    if score >= 2:
        return "BUY"
    elif score <= -2:
        return "SELL"
    return "HOLD"

# =========================
# RISK ENGINE
# =========================

def size(cash, price):
    risk = 0.05
    return max(int((cash * risk) / price), 1)

# =========================
# START SYSTEM
# =========================

if st.button("START AUTONOMOUS AI"):

    if api_key and api_secret:

        api = tradeapi.REST(
            api_key,
            api_secret,
            base_url=base_url,
            api_version="v2"
        )

        account = api.get_account()
        cash = float(account.cash)

        st.success("AI SYSTEM ONLINE")

        bars = api.get_bars(symbol, "1Min", limit=30)
        prices = [b.c for b in bars]

        decision = brain(prices)

        price = prices[-1]
        qty = size(cash, price)

        st.subheader("AI Decision")
        st.write(decision)

        st.write("Price:", price)
        st.write("Qty:", qty)

        # =========================
        # EXECUTION
        # =========================

        if decision == "BUY":
            api.submit_order(symbol, qty, "buy", "market", "day")
            st.session_state.log.append(f"{datetime.now()} BUY {qty}")

        elif decision == "SELL":
            api.submit_order(symbol, qty, "sell", "market", "day")
            st.session_state.log.append(f"{datetime.now()} SELL {qty}")

        # =========================
        # MEMORY
        # =========================

        st.subheader("Trade Memory")

        for item in st.session_state.log[-10:]:
            st.write(item)

        # =========================
        # PORTFOLIO
        # =========================

        st.subheader("Portfolio")

        positions = api.list_positions()

        for p in positions:
            st.write(f"{p.symbol} | {p.qty} | PnL: {p.unrealized_pl}")

    else:
        st.warning("Enter API keys")