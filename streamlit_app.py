import streamlit as st
import alpaca_trade_api as tradeapi

st.title("📊 Trading Dashboard")

st.write("App running")

# =========================
# INPUT KEYS INSIDE APP
# =========================

api_key = st.text_input("API Key ID", type="password")
api_secret = st.text_input("API Secret Key", type="password")
base_url = st.selectbox(
    "Environment",
    ["https://paper-api.alpaca.markets", "https://api.alpaca.markets"]
)

api = None

# =========================
# CONNECT BUTTON
# =========================

if st.button("Connect to Alpaca"):

    if api_key and api_secret:
        try:
            api = tradeapi.REST(
                api_key,
                api_secret,
                base_url=base_url,
                api_version="v2"
            )

            account = api.get_account()

            st.success("Connected successfully")

            st.subheader("Account Info")
            st.write("Status:", account.status)
            st.write("Buying Power:", account.buying_power)
            st.write("Cash:", account.cash)

        except Exception as e:
            st.error("Connection failed")
            st.write(e)
    else:
        st.warning("Enter API key + secret first")