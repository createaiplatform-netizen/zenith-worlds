class Executor:

    def __init__(self, api):
        self.api = api

    def buy(self, symbol, qty):
        self.api.submit_order(symbol, qty, "buy", "market", "day")

    def sell(self, symbol, qty):
        self.api.submit_order(symbol, qty, "sell", "market", "day")