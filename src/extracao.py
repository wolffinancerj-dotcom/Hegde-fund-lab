from estrategias.media_movel import SmaCross
from estrategias.rsi_reversion import RsiReversion
from estrategias.bollinger_reversion import BollingerReversion
from src.backtest import backtest_quant
from backtesting import Backtest
from prefect import task, flow 

import yfinance as yf
import pandas as pd



@task
def download_carteira_close(ticket):
    ''' 
    Extração dos dados do ticker no período de um ano, com os dados já limpos.
        ticket
        Período: 5 ano fixo
        Apenas a coluna Close
    '''
    return yf.download(ticket, period='5y')['Close'].dropna()

@task
def download_carteira_OHLC(ticket):
    ''' 
    Extração dos dados do ticker no período de um ano, com os dados já limpos.
        ticket
        Período: 5 ano fixo
        Formato para a Backtesting OHLC
    '''
    df=yf.download(ticket, period='5y', multi_level_index=False).dropna()
    return df[['Open', 'High', 'Low', 'Close']]

@flow
def extracao():
    ticket = ['MSFT']
    df = download_carteira_OHLC(ticket)
    df=df.astype(float)
    backtest_quant(df)





