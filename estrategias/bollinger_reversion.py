from backtesting import Strategy
import pandas as pd

def BollingerBands(values, n=20, k=2):
    series = pd.Series(values)

    ma = series.rolling(n).mean()
    std = series.rolling(n).std()

    upper = ma + k * std
    lower = ma - k * std

    return upper, ma, lower


class BollingerReversion(Strategy):
    period = 20
    std_mult = 2

    
    def init(self):
        self.upper, self.middle, self.lower = self.I(
            BollingerBands,
            self.data.Close,
            self.period,
            self.std_mult
        )

    def next(self):
        price = self.data.Close[-1]

        # Compra quando rompe banda inferior
        if price < self.lower[-1] and not self.position:
            self.buy()

        # Sai quando volta para a média
        elif self.position and price >= self.middle[-1]:
            self.position.close()
