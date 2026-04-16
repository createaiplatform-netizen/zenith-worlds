import streamlit as st
import alpaca_trade_api as tradeapi

# =========================
# LOAD SECRETS (SAFE WAY)
# =========================

API_KEY = st.secrets["APCA_API_KEY_ID"]
API_SECRET = st.secrets["APCA_API_SECRET_KEY"]
BASE_URL = st.secrets.get("BASE_URL", "https://paper-api.alpaca.markets")

# =========================
# INIT CLIENT
# =========================

api = tradeapi.REST(
    API_KEY,
    API_SECRET,
    base_url=BASE_URL,
    api_version="v2"
)