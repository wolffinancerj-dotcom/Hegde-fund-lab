from estrategias.media_movel import SmaCross
from estrategias.rsi_reversion import RsiReversion
from estrategias.bollinger_reversion import BollingerReversion
from estrategias.buyandhold import BuyAndHold
from backtesting import Backtest

from prefect import task, flow 
import pandas as pd

@task
def backtest_quant(df):
    estrategias = {
        "Buy & Hold": BuyAndHold,
        "SMA Cross": SmaCross,
        "RSI Reversion": RsiReversion,
        "Bollinger Reversion": BollingerReversion

    }

    resultados = []

    for nome, estrategia in estrategias.items():
        bt = Backtest(
            df,
            estrategia,
            cash=10_000,
            commission=0.002
        )
        stats = bt.run()

        resultados.append({
            "Estratégia": nome,
            "Retorno (%)": round(stats["Return [%]"], 2),
            "Sharpe": round(stats["Sharpe Ratio"], 2),
            "Calmar": round(stats["Calmar Ratio"], 2),
            "Drawdown (%)": round(stats["Max. Drawdown [%]"], 2),
            "Trades": int(stats["# Trades"]),
            "Win Rate (%)": round(stats["Win Rate [%]"], 2),
            "Avg Trade (%)": round(stats["Avg. Trade [%]"], 2),
            "Profit Factor": round(stats["Profit Factor"], 2),
            "Expectancy": round(stats["Expectancy [%]"], 2)
        })


    resumo = pd.DataFrame(resultados)
    print("\n" + "=" * 130)
    print(resumo.to_string(index=False))
    print("=" * 130)

    return resumo