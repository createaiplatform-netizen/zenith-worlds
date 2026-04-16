import streamlit as st
import requests

st.title("🧠 AI Trading Dashboard")

backend = st.text_input("Backend URL", "http://localhost:8000")
symbol = st.text_input("Symbol", "AAPL")

if st.button("Run One Cycle"):
    try:
        r = requests.get(f"{backend}/cycle", params={"symbol": symbol})
        st.write(r.json())
    except Exception as e:
        st.error(str(e))

if st.button("System Status"):
    try:
        r = requests.get(f"{backend}/status")
        st.write(r.json())
    except Exception as e:
        st.error(str(e))