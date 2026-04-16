import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np
import sqlite3
from datetime import datetime

st.title("🧠 AI Trading Brain (Single File Version)")

# =========================
# INPUTS
# =========================

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("API Secret", type="password")

symbol = st.text_input("Symbol", "AAPL")

base_url = "https://paper-api.alpaca.markets"

# =========================
# MEMORY (NO BACKEND NEEDED)
# =========================

conn = sqlite3.connect("trades.db", check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS trades (
    time TEXT,
    symbol TEXT,
    side TEXT,
    qty INTEGER
)
""")

def log_trade(symbol, side, qty):
    conn.execute(
        "INSERT INTO trades VALUES (?, ?, ?, ?)",
        (str(datetime.now()), symbol, side, qty)
    )
    conn.commit()

# =========================
# AI BRAIN
# =========================

def brain(prices):
    prices = np.array(prices)

    short = np.mean(prices[-5:])
    long = np.mean(prices[-20:])
    momentum = prices[-3] - prices[-10]

    score = 0
    score += 1 if short > long else -1
    score += 1 if momentum > 0 else -1

    if score >= 2:
        return "BUY"
    elif score <= -2:
        return "SELL"
    return "HOLD"

# =========================
# POSITION SIZE
# =========================

def size(cash, price):
    return max(int((cash * 0.05) / price), 1)

# =========================
# RUN SYSTEM
# =========================

if st.button("RUN AI CYCLE"):

    if api_key and api_secret:

        api = tradeapi.REST(
            api_key,
            api_secret,
            base_url=base_url,
            api_version="v2"
        )

        account = api.get_account()
        cash = float(account.cash)

        st.success("Connected")

        bars = api.get_bars(symbol, "1Min", limit=30)
        prices = [b.c for b in bars]

        decision = brain(prices)
        price = prices[-1]
        qty = size(cash, price)

        st.write("Decision:", decision)
        st.write("Price:", price)
        st.write("Qty:", qty)

        if decision == "BUY":
            api.submit_order(symbol, qty, "buy", "market", "day")
            log_trade(symbol, "BUY", qty)
            st.success("BUY SENT")

        elif decision == "SELL":
            api.submit_order(symbol, qty, "sell", "market", "day")
            log_trade(symbol, "SELL", qty)
            st.success("SELL SENT")

        st.subheader("Trade History")

        rows = conn.execute("SELECT * FROM trades ORDER BY time DESC LIMIT 10").fetchall()

        for r in rows:
            st.write(r)

    else:
        st.warning("Enter API keys")