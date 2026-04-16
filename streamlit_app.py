import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np
import sqlite3
import time
from datetime import datetime

st.title("🧠 Autonomous AI Trading System (Advanced Single File)")

# =========================
# INPUTS
# =========================

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("API Secret", type="password")
symbol = st.text_input("Symbol", "AAPL")

base_url = "https://paper-api.alpaca.markets"

# =========================
# MEMORY DATABASE (PERSISTENT)
# =========================

conn = sqlite3.connect("trades.db", check_same_thread=False)
conn.execute("""
CREATE TABLE IF NOT EXISTS trades (
    time TEXT,
    symbol TEXT,
    action TEXT,
    qty INTEGER,
    price REAL
)
""")

def log_trade(symbol, action, qty, price):
    conn.execute(
        "INSERT INTO trades VALUES (?, ?, ?, ?, ?)",
        (str(datetime.now()), symbol, action, qty, price)
    )
    conn.commit()

def get_trades():
    return conn.execute(
        "SELECT * FROM trades ORDER BY time DESC LIMIT 10"
    ).fetchall()

# =========================
# AI BRAIN
# =========================

def brain(prices):
    prices = np.array(prices)

    if len(prices) < 20:
        return "HOLD"

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
# POSITION SIZING
# =========================

def size(cash, price):
    risk = 0.01
    return max(int((cash * risk) / price), 1)

# =========================
# STATE CONTROL
# =========================

if "running" not in st.session_state:
    st.session_state.running = False

if st.button("START AUTONOMOUS AI"):
    st.session_state.running = True

if st.button("STOP AI"):
    st.session_state.running = False

# =========================
# MAIN SYSTEM LOOP (SIMULATED)
# =========================

if api_key and api_secret:

    api = tradeapi.REST(
        api_key,
        api_secret,
        base_url,
        api_version="v2"
    )

    st.write("System Status:", "🟢 RUNNING" if st.session_state.running else "🔴 STOPPED")

    if st.session_state.running:

        try:
            account = api.get_account()
            cash = float(account.cash)

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
            # EXECUTION ENGINE
            # =========================

            if decision == "BUY":
                api.submit_order(symbol, qty, "buy", "market", "day")
                log_trade(symbol, "BUY", qty, price)
                st.success("BUY EXECUTED")

            elif decision == "SELL":
                api.submit_order(symbol, qty, "sell", "market", "day")
                log_trade(symbol, "SELL", qty, price)
                st.success("SELL EXECUTED")

            else:
                st.info("HOLD - no action")

        except Exception as e:
            st.error(str(e))

# =========================
# MEMORY DISPLAY
# =========================

st.subheader("📊 Trade History (Memory)")

trades = get_trades()

for t in trades:
    st.write(t)