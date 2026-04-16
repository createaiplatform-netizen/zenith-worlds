import streamlit as st
import pandas as pd
import numpy as np
import requests
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

class ZenithEngine:
    def __init__(self):
        self.model = IsolationForest(n_estimators=200, contamination=0.05, random_state=42)
        self.scaler = StandardScaler()

    def build(self, df):
        df = df.copy()
        df["log_return"] = np.log(df["Price"]).diff()
        df["volatility"] = df["log_return"].rolling(20).std()
        df["momentum"] = df["Price"].diff(5)
        return df.dropna()

    def analyze(self, df):
        df = self.build(df)

        X = self.scaler.fit_transform(df[["log_return", "volatility", "momentum"]])

        self.model.fit(X)

        df["anomaly"] = self.model.predict(X)
        df["score"] = -self.model.decision_function(X)

        last = df.iloc[-1]

        if last["anomaly"] == -1:
            state = "🚀 EXPANSION" if last["momentum"] > 0 else "⚠️ DISTRIBUTION"
        else:
            state = "⚖️ EQUILIBRIUM"

        return df, state, float(last["score"])


@st.cache_data
def load():
    url = "https://api.coingecko.com/api/v3/coins/ripple/market_chart"
    params = {"vs_currency": "usd", "days": 30}
    r = requests.get(url, params=params).json()

    df = pd.DataFrame(r["prices"], columns=["ts", "Price"])
    df["Date"] = pd.to_datetime(df["ts"], unit="ms")
    return df


st.title("Zenith — Market Sensor")

engine = ZenithEngine()

df = load()
data, state, score = engine.analyze(df)

c1, c2, c3 = st.columns(3)

c1.metric("State", state)
c2.metric("Score", f"{score:.4f}")
c3.metric("Price", f"${df['Price'].iloc[-1]:.4f}")

st.line_chart(data.set_index("Date")[["Price", "score"]])