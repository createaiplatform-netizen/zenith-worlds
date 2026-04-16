import numpy as np
import pandas as pd
import requests
import yfinance as yf
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

# =========================
# LIQUIDITY INTELLIGENCE ENGINE
# =========================

class LiquidityEngine:
    def __init__(self):
        self.scaler = StandardScaler()
        self.model = IsolationForest(
            n_estimators=300,
            contamination=0.05,
            random_state=42
        )

    # -------------------------
    # DATA COLLECTION LAYER
    # -------------------------
    def get_macro_data(self):
        try:
            dxy = yf.download("DX-Y.NYB", period="3mo")["Close"]
            vix = yf.download("^VIX", period="3mo")["Close"]
            spx = yf.download("^GSPC", period="3mo")["Close"]
            btc = yf.download("BTC-USD", period="3mo")["Close"]

            df = pd.DataFrame({
                "dxy": dxy,
                "vix": vix,
                "spx": spx,
                "btc": btc
            }).dropna()

            return df

        except Exception:
            return pd.DataFrame()

    # -------------------------
    # FEATURE ENGINEERING
    # -------------------------
    def features(self, df):
        df = df.copy()

        df["dxy_change"] = df["dxy"].pct_change()
        df["vix_change"] = df["vix"].pct_change()
        df["spx_return"] = df["spx"].pct_change()
        df["btc_return"] = df["btc"].pct_change()

        df["risk_on"] = df["spx_return"] + df["btc_return"]
        df["risk_off"] = df["dxy_change"] + df["vix_change"]

        df["liquidity_proxy"] = df["risk_on"] - df["risk_off"]

        df = df.dropna()
        return df

    # -------------------------
    # INTELLIGENCE CORE
    # -------------------------
    def analyze(self, df):
        df = self.features(df)

        X = self.scaler.fit_transform(
            df[[
                "dxy_change",
                "vix_change",
                "spx_return",
                "btc_return",
                "liquidity_proxy"
            ]]
        )

        self.model.fit(X)

        df["anomaly"] = self.model.predict(X)
        df["score"] = -self.model.decision_function(X)

        last = df.iloc[-1]

        # -------------------------
        # REGIME LOGIC
        # -------------------------
        if last["liquidity_proxy"] > 0.002:
            regime = "🟢 LIQUIDITY EXPANDING"
        elif last["liquidity_proxy"] < -0.002:
            regime = "🔴 LIQUIDITY CONTRACTING"
        else:
            regime = "🟡 NEUTRAL FLOW"

        confidence = float(min(1.0, abs(last["score"])))

        return df, regime, confidence


# =========================
# STANDALONE TEST
# =========================
if __name__ == "__main__":
    engine = LiquidityEngine()
    df = engine.get_macro_data()

    if not df.empty:
        data, regime, conf = engine.analyze(df)
        print("REGIME:", regime)
        print("CONFIDENCE:", conf)