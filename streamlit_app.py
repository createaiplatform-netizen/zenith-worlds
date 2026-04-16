import streamlit as st
import random
import hashlib
import pandas as pd
import numpy as np

# --- 1. CORE ARCHITECTURE & THEME ---
st.set_page_config(page_title="Zenith Worlds", page_icon="🪐", layout="wide")

# Custom CSS to match the Zenith aesthetic
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. THE "LITTLE AI" PROTOCOL ---
def get_resident_ai(seed):
    """Every product has its own AI that changes based on the seed."""
    random.seed(seed)
    names = ["Astra", "Echo", "Nova", "Quark", "Zen"]
    moods = ["Calculating", "Harmonious", "Vigilant", "Inquisitive"]
    return {
        "name": random.choice(names),
        "mood": random.choice(moods),
        "message": f"Welcome to this coordinate. I have stabilized the local mathematical constants for you."
    }

# --- 3. DETERMINISTIC ENGINE (The Math) ---
def generate_world(seed):
    # Hash the seed to get a consistent unique number
    hash_object = hashlib.sha256(seed.encode())
    hex_dig = hash_object.hexdigest()
    num_seed = int(hex_dig[:8], 16)
    random.seed(num_seed)
    
    return {
        "altitude": random.randint(100, 8000),
        "gravity": round(random.uniform(0.1, 2.5), 2),
        "bioluminescence": random.choice(["Active", "Dormant", "Pulsing"]),
        "complexity": random.randint(1, 100),
        "points": np.random.normal(0, 1, size=100).cumsum() # Terrain Data
    }

# --- 4. THE INTERFACE ---
st.title("ZENITH WORLDS 🚀")
st.subheader("The Deterministic World-Sharing Platform")

# Sidebar - The Entry Point
st.sidebar.title("📡 Transmission")
world_id = st.sidebar.text_input("Enter World Seed / URL ID", value="Genesis-Prime")
st.sidebar.caption("Share this ID with anyone to show them this exact world.")

# Process World Data
world = generate_world(world_id)
ai = get_resident_ai(world_id)

# Main Display
col1, col2 = st.columns([2, 1])

with col1:
    st.header(f"📍 World: {world_id}")
    
    # Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Altitude", f"{world['altitude']}m")
    m2.metric("Gravity", f"{world['gravity']}G")
    m3.metric("Bioluminescence", world['bioluminescence'])
    
    # Mathematical Terrain Visualization
    st.write("### 📉 Terrain Frequency Analysis")
    st.line_chart(world['points'])
    
    if st.button("❤️ Like & Archive to Global Registry"):
        st.balloons()
        st.success(f"World {world_id} saved to the Zenith Registry!")

with col2:
    # The Resident AI UI
    st.markdown(f"### 🤖 AI Resident: {ai['name']}")
    st.info(f"**Current State:** {ai['mood']}\n\n*{ai['message']}*")
    
    st.write("---")
    st.write("**World Integrity**")
    st.progress(world['complexity'] / 100)
    st.caption("Mathematical stability of this generation.")

# --- 5. SOCIAL DISCOVERY FEED (The Registry) ---
st.divider()
st.subheader("🛰️ Global Discovery Feed (Live Registry)")
# Mock registry data representing the network effect
registry_data = {
    "World ID": ["Void-Runner", "Oceania-7", "Sara-1", world_id],
    "Likes": [1024, 856, 2100, 1],
    "Stability": ["99%", "94%", "100%", f"{world['complexity']}%"]
}
st.table(pd.DataFrame(registry_data))

st.caption("Zenith Worlds v1.0 | Deterministic Architecture | No Bloat")
