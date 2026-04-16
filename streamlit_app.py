import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np
import pandas as pd
import time
import json
from datetime import datetime
import os

st.set_page_config(page_title="Autonomous AI Brain FINAL", layout="wide")

st.title("🧠 Autonomous AI Trading Brain (Final System)")

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
# PERSISTENT MEMORY (FILE)
# =========================

MEMORY_FILE = "trade_memory.json"

if os.path.exists(MEMORY_FILE):
    with open(MEMORY_FILE, "r") as f:
        memory = json.load(f)
else:
    memory = {"trades": [], "pnl": 0}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f)

# =========================
# RISK ENGINE (REAL RULES)
# =========================

MAX_DAILY_LOSS = -200
MAX_EXPOSURE = 0.2  # 20% capital max

def risk_check(pnl):
    if pnl <= MAX_DAILY_LOSS:
        return False
    return True

# =========================
# AI BRAIN (ENSEMBLE)
# =========================

def ai_brain(prices):
    prices = np.array(prices)

    short = np.mean(prices[-5:])
    mid = np.mean(prices[-10:])
    long = np.mean(prices[-20:])

    momentum = prices[-1] - prices[-4]
    volatility = np.std(prices[-15:])

    vote = 0

    # trend stack
    vote += 1 if short > mid else -1
    vote += 1 if mid > long else -1

    # momentum
    vote += 1 if momentum > 0 else -1

    # volatility penalty
    if volatility > np.mean(prices[-15:]) * 0.03:
        vote -= 1

    if vote >= 2:
        return "BUY", vote
    elif vote <= -2:
        return "SELL", vote
    return "HOLD", vote

# =========================
# POSITION SIZING
# =========================

def position_size(cash, price):
    return max(int((cash * MAX_EXPOSURE) / price), 1)

# =========================
# CONNECT
# =========================

api = None

if st.button("RUN AUTONOMOUS CYCLE"):

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

            st.success("SYSTEM ONLINE")

            col1, col2, col3 = st.columns(3)
            col1.metric("Cash", account.cash)
            col2.metric("Status", account.status)
            col3.metric("Memory Trades", len(memory["trades"]))

            # =========================
            # MARKET DATA
            # =========================

            bars = api.get_bars(symbol, "1Min", limit=40)
            prices = [b.c for b in bars]

            decision, score = ai_brain(prices)

            st.subheader("🧠 AI Brain Output")
            st.write("Decision:", decision)
            st.write("Score:", score)

            price = prices[-1]
            qty = position_size(cash, price)

            st.write("Price:", price)
            st.write("Qty:", qty)

            # =========================
            # RISK CHECK
            # =========================

            if not risk_check(memory["pnl"]):
                st.error("🚨 KILL SWITCH ACTIVE (Daily loss limit reached)")
                st.stop()

            # =========================
            # EXECUTION ENGINE
            # =========================

            if decision == "BUY":
                order = api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side="buy",
                    type="market",
                    time_in_force="day"
                )

                memory["trades"].append(f"{datetime.now()} BUY {symbol} {qty}")
                save_memory()

                st.success("BUY EXECUTED")

            elif decision == "SELL":
                order = api.submit_order(
                    symbol=symbol,
                    qty=qty,
                    side="sell",
                    type="market",
                    time_in_force="day"
                )

                memory["trades"].append(f"{datetime.now()} SELL {symbol} {qty}")
                save_memory()

                st.success("SELL EXECUTED")

            else:
                st.info("HOLD")

            # =========================
            # PORTFOLIO
            # =========================

            st.subheader("📦 Portfolio")

            positions = api.list_positions()

            for p in positions:
                st.write(f"{p.symbol} | Qty: {p.qty} | P/L: {p.unrealized_pl}")

            # =========================
            # MEMORY VIEW
            # =========================

            st.subheader("🧠 Trade Memory")

            for t in memory["trades"][-10:]:
                st.write(t)

        except Exception as e:
            st.error(e)

    else:
        st.warning("Enter API keys")