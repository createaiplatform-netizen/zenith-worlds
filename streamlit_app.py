# execution.py

class Executor:

    def __init__(self, api):
        self.api = api

    def buy(self, symbol, qty):
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side="buy",
            type="market",
            time_in_force="day"
        )

    def sell(self, symbol, qty):
        return self.api.submit_order(
            symbol=symbol,
            qty=qty,
            side="sell",
            type="market",
            time_in_force="day"
        )