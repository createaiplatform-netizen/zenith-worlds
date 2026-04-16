import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np

st.title("🧠 Simple AI Trading Bot")

api_key = st.text_input("API Key", type="password")
api_secret = st.text_input("API Secret", type="password")

symbol = st.text_input("Symbol", "AAPL")

base_url = "https://paper-api.alpaca.markets"

def brain(prices):
    prices = np.array(prices)

    short = np.mean(prices[-5:])
    long = np.mean(prices[-20:])

    if short > long:
        return "BUY"
    elif short < long:
        return "SELL"
    return "HOLD"

if st.button("RUN AI"):

    if api_key and api_secret:

        api = tradeapi.REST(
            api_key,
            api_secret,
            base_url,
            api_version="v2"
        )

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
        st.warning("Enter API keys")