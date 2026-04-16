# risk.py

class RiskEngine:

    def __init__(self):
        self.max_daily_loss = -200
        self.exposure_limit = 0.2

    def allow_trade(self, pnl):
        return pnl > self.max_daily_loss

    def position_size(self, cash, price):
        return max(int((cash * self.exposure_limit) / price), 1)