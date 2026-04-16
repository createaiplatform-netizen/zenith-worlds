# server.py
from fastapi import FastAPI
import alpaca_trade_api as tradeapi

from brain import Brain
from execution import Executor
from risk import RiskEngine
from memory import Memory
from engine import Engine

app = FastAPI()

api = tradeapi.REST("KEY", "SECRET", "https://paper-api.alpaca.markets")

brain = Brain(api)
executor = Executor(api)
risk = RiskEngine()
memory = Memory()

engine = Engine(brain, executor, risk, memory, api)

@app.post("/cycle")
def cycle():
    return engine.cycle("AAPL")

@app.get("/status")
def status():
    return {"status": "AI Brain Active"}