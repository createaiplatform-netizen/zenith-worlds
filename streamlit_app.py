import streamlit as st

st.set_page_config(page_title="Trading App", layout="centered")

st.title("📊 Trading Dashboard")

st.write("App is running")

# =========================
# SAFE UI TEST
# =========================

st.subheader("System Check")
st.success("Streamlit is working")

st.button("Refresh")