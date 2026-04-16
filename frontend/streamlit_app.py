import streamlit as st
import requests

st.title("🧠 Autonomous Trading System Dashboard")

backend = st.text_input("Backend URL", "http://localhost:8000")
symbol = st.text_input("Symbol", "AAPL")

if st.button("Run Cycle"):
    r = requests.get(f"{backend}/cycle", params={"symbol": symbol})
    st.write(r.json())

if st.button("Status"):
    st.write("System connected")