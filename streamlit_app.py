import streamlit as st
import alpaca_trade_api as tradeapi

st.title("📊 Trading Dashboard")

st.write("App is running")

# =========================
# SECRETS
# =========================

API_KEY = st.secrets.get("APCA_API_KEY_ID")
API_SECRET = st.secrets.get("APCA_API_SECRET_KEY")
BASE_URL = st.secrets.get("BASE_URL", "https://paper-api.alpaca.markets")

# =========================
# CONNECT
# =========================

api = None

if API_KEY and API_SECRET:
    try:
        api = tradeapi.REST(
            API_KEY,
            API_SECRET,
            base_url=BASE_URL,
            api_version="v2"
        )
        st.success("Connected to Alpaca")
    except Exception as e:
        st.error("Connection failed")
        st.write(e)
else:
    st.warning("Missing API keys")

# =========================
# ACCOUNT
# =========================

if api:
    account = api.get_account()

    st.subheader("Account Info")
    st.write("Status:", account.status)
    st.write("Buying Power:", account.buying_power)
    st.write("Cash:", account.cash)

st.button("Refresh")