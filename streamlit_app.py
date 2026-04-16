# brain.py
import alpaca_trade_api as tradeapi
import numpy as np

class Brain:

    def __init__(self, api):
        self.api = api

    def get_prices(self, symbol):
        bars = self.api.get_bars(symbol, "1Min", limit=50)
        return [b.c for b in bars]

    def decide(self, prices):
        prices = np.array(prices)

        if len(prices) < 10:
            return "HOLD"

        short = prices[-5:].mean()
        long = prices[-20:].mean()

        if short > long:
            return "BUY"
        elif short < long:
            return "SELL"
        return "HOLD"