import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np

st.title("🧠 AI Trading Bot (Simple Mode)")

# =========================
# INPUTS
# =========================

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("API Secret", type="password")
symbol = st.text_input("Symbol", "AAPL")

base_url = "https://paper-api.alpaca.markets"

# =========================
# AI BRAIN
# =========================

def brain(prices):
    prices = np.array(prices)

    if len(prices) < 20:
        return "HOLD"

    short = np.mean(prices[-5:])
    long = np.mean(prices[-20:])

    if short > long:
        return "BUY"
    elif short < long:
        return "SELL"
    return "HOLD"

# =========================
# RUN BOT
# =========================

if st.button("RUN AI TRADE"):

    if not api_key or not api_secret:
        st.warning("Put API Key + Secret first")
        st.stop()

    api = tradeapi.REST(
        api_key,
        api_secret,
        base_url,
        api_version="v2"
    )

    try:
        account = api.get_account()
        cash = float(account.cash)

        bars = api.get_bars(symbol, "1Min", limit=30)
        prices = [b.c for b in bars]

        decision = brain(prices)
        price = prices[-1]

        qty = max(int((cash * 0.01) / price), 1)

        st.write("Decision:", decision)
        st.write("Price:", price)
        st.write("Qty:", qty)

        if decision == "BUY":
            api.submit_order(symbol, qty, "buy", "market", "day")
            st.success("BUY SENT")

        elif decision == "SELL":
            api.submit_order(symbol, qty, "sell", "market", "day")
            st.success("SELL SENT")

        else:
            st.info("HOLD - no trade")

    except Exception as e:
        st.error(str(e))