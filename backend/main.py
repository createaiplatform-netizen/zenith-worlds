from fastapi import FastAPI
import alpaca_trade_api as tradeapi

from brain import Brain
from execution import Executor
from risk import Risk
from memory import Memory

app = FastAPI()

api = tradeapi.REST(
    "API_KEY",
    "API_SECRET",
    "https://paper-api.alpaca.markets",
    api_version="v2"
)

brain = Brain(api)
executor = Executor(api)
risk = Risk()
memory = Memory()

@app.get("/status")
def status():
    return {"status": "online"}

@app.post("/cycle")
def cycle(symbol: str = "AAPL"):

    account = api.get_account()
    cash = float(account.cash)

    prices = brain.get_prices(symbol)
    decision = brain.decide(prices)

    price = prices[-1]
    qty = risk.size(cash, price)

    if decision == "BUY":
        executor.buy(symbol, qty)
        memory.log(symbol, "BUY", qty)

    elif decision == "SELL":
        executor.sell(symbol, qty)
        memory.log(symbol, "SELL", qty)

    return {
        "symbol": symbol,
        "decision": decision,
        "qty": qty,
        "price": price
    }