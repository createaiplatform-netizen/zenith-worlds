import streamlit as st
import alpaca_trade_api as tradeapi

# ==============================
# SAFE CONFIG LOADER
# ==============================

def get_config():
    """
    Pulls credentials safely from Streamlit Secrets.
    Falls back to environment variables if needed.
    """

    key = st.secrets.get("APCA_API_KEY_ID", None)
    secret = st.secrets.get("APCA_API_SECRET_KEY", None)
    base_url = st.secrets.get("BASE_URL", "https://paper-api.alpaca.markets")

    if not key or not secret:
        st.error("Missing Alpaca API credentials in Streamlit Secrets.")
        st.stop()

    return key, secret, base_url


# ==============================
# INIT ALPACA CLIENT
# ==============================

API_KEY, API_SECRET, BASE_URL = get_config()

api = tradeapi.REST(
    API_KEY,
    API_SECRET,
    base_url=BASE_URL,
    api_version="v2"
)


# ==============================
# TEST CONNECTION
# ==============================

def test_connection():
    try:
        account = api.get_account()
        return account
    except Exception as e:
        st.error(f"Alpaca connection failed: {e}")
        return None


# ==============================
# STREAMLIT UI
# ==============================

st.title("📊 Alpaca Trading Dashboard")

if st.button("Test Connection"):
    account = test_connection()

    if account:
        st.success("Connected to Alpaca successfully!")

        st.write("Account Status:", account.status)
        st.write("Buying Power:", account.buying_power)
        st.write("Cash:", account.cash)