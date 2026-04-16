import streamlit as st
import alpaca_trade_api as tradeapi

st.set_page_config(page_title="AI Trading System", layout="wide")

st.title("📊 AI Trading System Dashboard")

# =========================
# KEYS
# =========================

api_key = st.text_input("API Key ID", type="password")
api_secret = st.text_input("API Secret Key", type="password")

base_url = st.selectbox(
    "Environment",
    ["https://paper-api.alpaca.markets", "https://api.alpaca.markets"]
)

api = None

# =========================
# CONNECT
# =========================

if st.button("Initialize System"):

    if api_key and api_secret:

        try:
            api = tradeapi.REST(
                api_key,
                api_secret,
                base_url=base_url,
                api_version="v2"
            )

            account = api.get_account()

            st.success("System Online")

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Status", account.status)

            with col2:
                st.metric("Buying Power", account.buying_power)

            with col3:
                st.metric("Cash", account.cash)

            # =========================
            # POSITIONS
            # =========================

            st.subheader("📦 Open Positions")

            positions = api.list_positions()

            if positions:
                for p in positions:
                    st.write(f"{p.symbol} | Qty: {p.qty} | P/L: {p.unrealized_pl}")
            else:
                st.write("No open positions")

        except Exception as e:
            st.error("System failed to initialize")
            st.write(e)

    else:
        st.warning("Missing credentials")

# =========================
# TRADING PANEL
# =========================

st.subheader("💱 Trade Panel")

symbol = st.text_input("Symbol (e.g. AAPL)")
qty = st.number_input("Quantity", min_value=1, step=1)

col1, col2 = st.columns(2)

with col1:
    if st.button("BUY"):
        try:
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="buy",
                type="market",
                time_in_force="day"
            )
            st.success(f"BUY order sent: {symbol}")
        except Exception as e:
            st.error(e)

with col2:
    if st.button("SELL"):
        try:
            api.submit_order(
                symbol=symbol,
                qty=qty,
                side="sell",
                type="market",
                time_in_force="day"
            )
            st.success(f"SELL order sent: {symbol}")
        except Exception as e:
            st.error(e)