import numpy as np

class Brain:

    def __init__(self, api):
        self.api = api

    def get_prices(self, symbol):
        bars = self.api.get_bars(symbol, "1Min", limit=50)
        return [b.c for b in bars]

    def decide(self, prices):
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