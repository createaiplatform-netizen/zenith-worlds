import streamlit as st
import alpaca_trade_api as tradeapi

st.title("📊 Trading Dashboard")

st.write("App is running")

API_KEY = st.secrets.get("APCA_API_KEY_ID")
API_SECRET = st.secrets.get("APCA_API_SECRET_KEY")
BASE_URL = st.secrets.get("BASE_URL", "https://paper-api.alpaca.markets")

st.write("Keys loaded:", bool(API_KEY and API_SECRET))

api = None

# =========================
# CREATE CLIENT
# =========================

try:
    api = tradeapi.REST(
        API_KEY,
        API_SECRET,
        base_url=BASE_URL,
        api_version="v2"
    )
    st.success("Client created")
except Exception as e:
    st.error("Client creation failed")
    st.write(e)

# =========================
# SAFE ACCOUNT CALL
# =========================

if api:
    try:
        account = api.get_account()

        st.success("Connected to Alpaca")

        st.subheader("Account Info")
        st.write("Status:", account.status)
        st.write("Buying Power:", account.buying_power)
        st.write("Cash:", account.cash)

    except Exception as e:
        st.error("ALPACA REJECTED REQUEST")

        st.write("Error type:", type(e).__name__)
        st.write("Error details:", str(e))

st.button("Refresh")