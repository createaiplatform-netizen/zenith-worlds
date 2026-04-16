import streamlit as st
import alpaca_trade_api as tradeapi

st.title("📊 Trading Dashboard")

api_key = st.text_input("API Key ID", type="password")
api_secret = st.text_input("API Secret Key", type="password")

base_url = st.selectbox(
    "Environment",
    ["https://paper-api.alpaca.markets", "https://api.alpaca.markets"]
)

api = None

if st.button("Connect & Load Account"):

    if api_key and api_secret:
        try:
            api = tradeapi.REST(
                api_key,
                api_secret,
                base_url=base_url,
                api_version="v2"
            )

            account = api.get_account()

            st.success("Connected")

            st.subheader("Account Info")
            st.write("Status:", account.status)
            st.write("Buying Power:", account.buying_power)
            st.write("Cash:", account.cash)

        except Exception as e:
            st.error("Connection failed")
            st.write(e)

    else:
        st.warning("Enter both API Key and Secret")