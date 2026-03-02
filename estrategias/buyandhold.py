from backtesting import Strategy

class BuyAndHold(Strategy):
    def init(self):
        # No indicators needed
        pass

    def next(self):
        # If we don't have a position, buy as much as possible
        if not self.position:
            self.buy()