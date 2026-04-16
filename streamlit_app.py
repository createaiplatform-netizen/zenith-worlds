# engine.py

class Engine:

    def __init__(self, brain, executor, risk, memory, api):
        self.brain = brain
        self.executor = executor
        self.risk = risk
        self.memory = memory
        self.api = api

    def cycle(self, symbol):

        account = self.api.get_account()
        cash = float(account.cash)

        prices = self.brain.get_prices(symbol)
        decision = self.brain.decide(prices)

        price = prices[-1]
        qty = self.risk.position_size(cash, price)

        if decision == "BUY":
            self.executor.buy(symbol, qty)
            self.memory.log(symbol, "BUY", qty)

        elif decision == "SELL":
            self.executor.sell(symbol, qty)
            self.memory.log(symbol, "SELL", qty)

        return {"decision": decision, "qty": qty}