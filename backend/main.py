from fastapi import FastAPI
import alpaca_trade_api as tradeapi
import numpy as np
import os

app = FastAPI()

api = tradeapi.REST(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_API_SECRET"),
    "https://paper-api.alpaca.markets",
    api_version="v2"
)

def brain(prices):
    prices = np.array(prices)

    short = np.mean(prices[-5:])
    long = np.mean(prices[-20:])
    momentum = prices[-3] - prices[-10]

    score = 0
    score += 1 if short > long else -1
    score += 1 if momentum > 0 else -1

    if score >= 2:
        return "BUY"
    elif score <= -2:
        return "SELL"
    return "HOLD"

@app.get("/cycle")
def cycle(symbol: str = "AAPL"):

    account = api.get_account()
    cash = float(account.cash)

    bars = api.get_bars(symbol, "1Min", limit=30)
    prices = [b.c for b in bars]

    decision = brain(prices)
    price = prices[-1]
    qty = max(int((cash * 0.01) / price), 1)

    if decision == "BUY":
        api.submit_order(symbol, qty, "buy", "market", "day")

    elif decision == "SELL":
        api.submit_order(symbol, qty, "sell", "market", "day")

    return {
        "symbol": symbol,
        "decision": decision,
        "qty": qty,
        "price": price
    }