import streamlit as st
import alpaca_trade_api as tradeapi
import numpy as np
import pandas as pd

st.set_page_config(page_title="AI Brain Trading System", layout="wide")

st.title("🧠 AI Brain Trading System")

# =========================
# INPUT CREDENTIALS
# =========================

api_key = st.text_input("API Key ID", type="password")
api_secret = st.text_input("API Secret Key", type="password")

base_url = st.selectbox(
    "Environment",
    ["https://paper-api.alpaca.markets", "https://api.alpaca.markets"]
)

# =========================
# AI STRATEGY ENGINE
# =========================

def ai_decision(prices):
    """
    Simple AI-like momentum + mean reversion hybrid brain.
    Returns BUY / SELL / HOLD
    """

    if len(prices) < 5:
        return "HOLD"

    recent = np.array(prices[-5:])
    mean = np.mean(recent)
    last = recent[-1]

    momentum = last - recent[0]

    if momentum > 0 and last > mean:
        return "BUY"
    elif momentum < 0 and last < mean:
        return "SELL"
    else:
        return "HOLD"


# =========================
# RISK ENGINE
# =========================

def position_size(cash, price):
    risk_per_trade = 0.05  # 5% risk model
    size_value = cash * risk_per_trade
    qty = max(int(size_value / price), 1)
    return qty


# =========================
# CONNECT
# =========================

api = None

if st.button("Activate AI Brain"):

    if api_key and api_secret:

        try:
            api = tradeapi.REST(
                api_key,
                api_secret,
                base_url=base_url,
                api_version="v2"
            )

            account = api.get_account()

            st.success("AI Brain Online")

            cash = float(account.cash)

            col1, col2, col3 = st.columns(3)

            col1.metric("Status", account.status)
            col2.metric("Buying Power", account.buying_power)
            col3.metric("Cash", account.cash)

            # =========================
            # MARKET DATA SIMULATION
            # =========================

            st.subheader("📈 AI Market Signal Engine")

            symbol = st.text_input("Symbol", "AAPL")

            bars = api.get_bars(symbol, "1Min", limit=20)
            prices = [b.c for b in bars]

            decision = ai_decision(prices)

            st.write("AI Decision:", decision)

            # =========================
            # EXECUTION ENGINE
            # =========================

            current_price = prices[-1]
            qty = position_size(cash, current_price)

            st.write("Suggested Position Size:", qty)

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
                st.info("NO ACTION (HOLD)")

            # =========================
            # POSITIONS VIEW
            # =========================

            st.subheader("📦 Portfolio")

            positions = api.list_positions()

            for p in positions:
                st.write(f"{p.symbol} | Qty: {p.qty} | P/L: {p.unrealized_pl}")

        except Exception as e:
            st.error("AI Brain Failed")
            st.write(e)

    else:
        st.warning("Enter API credentials")