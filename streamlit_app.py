import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Ultra AI Trading Brain", layout="wide")

st.title("🧠 Ultra AI Trading Brain System")

# =========================
# INPUT KEYS
# =========================

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("API Secret", type="password")

base_url = st.selectbox(
    "Environment",
    ["https://paper-api.alpaca.markets", "https://api.alpaca.markets"]
)

# =========================
# GLOBAL SAFETY SETTINGS
# =========================

MAX_RISK_PER_TRADE = 0.05   # 5%
MAX_DAILY_LOSS = 100        # hard stop (paper logic guard)
TRADE_LOCK = False

# =========================
# AI CORE ENGINE
# =========================

def brain(prices):
    prices = np.array(prices)

    if len(prices) < 10:
        return "HOLD", 0

    short_ma = np.mean(prices[-5:])
    long_ma = np.mean(prices[-10:])
    momentum = prices[-1] - prices[-3]

    score = 0

    # trend
    if short_ma > long_ma:
        score += 1
    else:
        score -= 1

    # momentum
    if momentum > 0:
        score += 1
    else:
        score -= 1

    # volatility check
    vol = np.std(prices[-10:])
    if vol > np.mean(prices[-10:]) * 0.02:
        score -= 1

    if score >= 2:
        return "BUY", score
    elif score <= -2:
        return "SELL", score
    else:
        return "HOLD", score


# =========================
# RISK ENGINE
# =========================

def position_size(cash, price):
    risk_amount = cash * MAX_RISK_PER_TRADE
    qty = max(int(risk_amount / price), 1)
    return qty


# =========================
# CONNECT
# =========================

api = None

if st.button("START AI BRAIN"):

    if api_key and api_secret:

        try:
            api = tradeapi.REST(
                api_key,
                api_secret,
                base_url=base_url,
                api_version="v2"
            )

            account = api.get_account()

            st.success("AI Brain ONLINE")

            cash = float(account.cash)

            col1, col2, col3 = st.columns(3)

            col1.metric("Status", account.status)
            col2.metric("Buying Power", account.buying_power)
            col3.metric("Cash", account.cash)

            # =========================
            # SYMBOL INPUT
            # =========================

            symbol = st.text_input("Symbol", "AAPL")

            bars = api.get_bars(symbol, "1Min", limit=50)
            prices = [b.c for b in bars]

            decision, score = brain(prices)

            st.subheader("🧠 AI Decision Engine")
            st.write("Decision:", decision)
            st.write("Confidence Score:", score)

            current_price = prices[-1]
            qty = position_size(cash, current_price)

            st.write("Price:", current_price)
            st.write("Position Size:", qty)

            # =========================
            # EXECUTION LAYER
            # =========================

            st.subheader("⚡ Execution Layer")

            if decision == "BUY":
                if st.button("EXECUTE BUY"):
                    api.submit_order(
                        symbol=symbol,
                        qty=qty,
                        side="buy",
                        type="market",
                        time_in_force="day"
                    )
                    st.success("BUY EXECUTED")

            elif decision == "SELL":
                if st.button("EXECUTE SELL"):
                    api.submit_order(
                        symbol=symbol,
                        qty=qty,
                        side="sell",
                        type="market",
                        time_in_force="day"
                    )
                    st.success("SELL EXECUTED")

            else:
                st.info("HOLD POSITION")

            # =========================
            # PORTFOLIO
            # =========================

            st.subheader("📦 Portfolio")

            positions = api.list_positions()

            for p in positions:
                st.write(f"{p.symbol} | Qty: {p.qty} | P/L: {p.unrealized_pl}")

        except Exception as e:
            st.error("AI Brain failure")
            st.write(e)

    else:
        st.warning("Enter API keys")