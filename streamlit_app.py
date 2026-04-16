import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np

st.title("🧠 Autonomous Trading Bot (Buttonless Version)")

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("API Secret", type="password")
symbol = st.text_input("Symbol", "AAPL")

base_url = "https://paper-api.alpaca.markets"

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

def run_bot(api, symbol):
    account = api.get_account()
    cash = float(account.cash)

    bars = api.get_bars(symbol, "1Min", limit=30)
    prices = [b.c for b in bars]

    decision = brain(prices)
    price = prices[-1]
    qty = max(int((cash * 0.01) / price), 1)

    return decision, price, qty, api, symbol

if "running" not in st.session_state:
    st.session_state.running = False

if st.button("START AUTONOMOUS MODE"):
    st.session_state.running = True

if st.button("STOP"):
    st.session_state.running = False

if api_key and api_secret:
    api = tradeapi.REST(
        api_key,
        api_secret,
        base_url,
        api_version="v2"
    )

    st.write("System Status:", "RUNNING" if st.session_state.running else "STOPPED")

    if st.session_state.running:

        decision, price, qty, api, symbol = run_bot(api, symbol)

        st.write("Decision:", decision)
        st.write("Price:", price)
        st.write("Qty:", qty)

        if decision == "BUY":
            api.submit_order(symbol, qty, "buy", "market", "day")
            st.success("BUY EXECUTED")

        elif decision == "SELL":
            api.submit_order(symbol, qty, "sell", "market", "day")
            st.success("SELL EXECUTED")

        else:
            st.info("HOLD")

    st.experimental_rerun()