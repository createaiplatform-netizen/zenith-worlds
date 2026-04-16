import streamlit as st
import requests

st.title("🧠 AI Trading Dashboard")

backend = st.text_input("Backend URL", "http://localhost:8000")

if st.button("Run Cycle"):
    r = requests.post(f"{backend}/cycle", params={"symbol": "AAPL"})
    st.write(r.json())

if st.button("Status"):
    r = requests.get(f"{backend}/status")
    st.write(r.json())