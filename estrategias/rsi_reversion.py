from backtesting import Strategy
import pandas as pd

def RSI(values, n=14):
    delta = pd.Series(values).diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(n).mean()
    avg_loss = loss.rolling(n).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


class RsiReversion(Strategy):
    rsi_period = 14
    rsi_low = 30
    rsi_high = 70

    
    def init(self):
        self.rsi = self.I(RSI, self.data.Close, self.rsi_period)

    def next(self):
        # Compra em sobrevenda
        if self.rsi[-1] < self.rsi_low and not self.position:
            self.buy()

        # Vende em sobrecompra
        elif self.rsi[-1] > self.rsi_high and self.position:
            self.position.close()
