class Risk:

    def __init__(self):
        self.risk_per_trade = 0.05

    def size(self, cash, price):
        return max(int((cash * self.risk_per_trade) / price), 1)