# streamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import hashlib
import random

# --- 1. CONFIGURATION & THEME ---
st.set_page_config(
    page_title="Zenith Data Systems",
    page_icon="🪐",
    layout="wide"
)

# Production-ready CSS
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
def generate_deterministic_data(seed):
    """Generates consistent simulated data based on a user-provided string."""
    hash_object = hashlib.sha256(seed.encode())
    num_seed = int(hash_object.hexdigest()[:8], 16)
    random.seed(num_seed)
    np.random.seed(num_seed)
    
    return {
        "node_id": seed.upper(),
        "performance_index": random.randint(85, 100),
        "network_latency": round(random.uniform(10.5, 95.2), 2),
        "system_gravity": round(random.uniform(0.1, 2.5), 2),
        "altitude_m": random.randint(100, 9000),
        "stream_data": np.random.normal(0, 1, size=100).cumsum()
    }

# --- 3. SIDEBAR CONTROLS ---
st.sidebar.title("📡 System Control")
user_identity = st.sidebar.text_input("User Identity", value="Sara Stadler")
node_input = st.sidebar.text_input("Project Node / Seed", value="Genesis-Prime")

st.sidebar.divider()
if st.sidebar.button("Refresh System Feed"):
    st.rerun()

# --- 4. MAIN INTERFACE ---
st.title("🪐 ZENITH DATA SYSTEMS")
st.caption(f"Authenticated User: {user_identity} | Node: {node_input}")

# Process Data
data = generate_deterministic_data(node_input)

# Top Level Metrics
m1, m2, m3 = st.columns(3)
m1.metric("System Stability", f"{data['performance_index']}%", delta="Stable")
m2.metric("Network Latency", f"{data['network_latency']}ms")
m3.metric("Node Reach", "Global Cluster")

# Content Grid
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 Infrastructure Analysis")
    st.line_chart(data['stream_data'])
    
    st.subheader("🌍 Sector Saturation")
    saturation_df = pd.DataFrame({
        'Sector': ['Compute', 'Storage', 'Network', 'Identity', 'Energy'],
        'Capacity %': [100, 98, 100, 95, 92]
    })
    st.bar_chart(saturation_df, x='Sector', y='Capacity %')

with col2:
    st.subheader("⚙️ Node Parameters")
    st.write(f"**ID:** {data['node_id']}")
    st.metric("Altitude", f"{data['altitude_m']}m")
    st.metric("Gravity Constant", f"{data['system_gravity']}G")
    
    st.divider()
    st.info("**System Note:** All data streams are synchronized with the deterministic core.")
    st.progress(data['performance_index'] / 100)

# --- 5. SYSTEM REGISTRY ---
st.divider()
st.subheader("🛰️ Active Registry")
registry_data = pd.DataFrame({
    "Node ID": ["ZENITH-01", "ALPHA-NODE", "SARA-MASTER", "GRID-7"],
    "Status": ["Online", "Online", "Anchored", "Active"],
    "Region": ["North America", "Europe", "Global Core", "Satellite"]
})
st.table(registry_data)

st.caption("Zenith Worlds | Production v2.1 | Streamlit Deployment Ready")
