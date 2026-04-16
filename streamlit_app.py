# streamlit_app.py
import streamlit as st
import requests

st.title("🧠 AI Brain Dashboard")

api_url = st.text_input("Backend URL", "http://localhost:8000")

if st.button("Start Brain Cycle"):
    r = requests.post(f"{api_url}/cycle")
    st.write(r.json())

if st.button("Get Status"):
    r = requests.get(f"{api_url}/status")
    st.write(r.json())