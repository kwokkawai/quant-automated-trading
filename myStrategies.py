
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from talib import SMA
import pandas as pd
import talib

class ADXStrategy(Strategy):
    adx_period = 14
    di_period = 14
    adx_threshold = 25
    exit_threshold = 20

    def init(self):
        high = self.data.High
        low = self.data.Low
        close = self.data.Close
        
        self.adx = self.I(talib.ADX, high, low, close, self.adx_period)
        self.plus_di = self.I(talib.PLUS_DI, high, low, close, self.di_period)
        self.minus_di = self.I(talib.MINUS_DI, high, low, close, self.di_period)

    def next(self):
        if crossover(self.plus_di, self.minus_di) and self.adx[-1] > self.adx_threshold:
            self.buy()
        elif crossover(self.minus_di, self.plus_di) and self.adx[-1] > self.adx_threshold:
            self.sell()

        for trade in self.trades:
            if trade.is_long and (
                crossover(self.minus_di, self.plus_di)
                or self.adx[-1] < self.exit_threshold
            ):
                trade.close()
            elif trade.is_short and (
                crossover(self.plus_di, self.minus_di)
                or self.adx[-1] < self.exit_threshold
            ):
                trade.close()

class BollingerBandsStrategy(Strategy):
    n1 = 20  # period for the SMA
    n2 = 50  # period for the trend filter SMA
    n_std_dev = 2

    def init(self):
        self.sma = self.I(SMA, self.data.Close, self.n1)
        self.upper_band = self.I(lambda data: SMA(data, self.n1) + self.n_std_dev * pd.Series(data).rolling(self.n1).std(), self.data.Close)
        self.lower_band = self.I(lambda data: SMA(data, self.n1) - self.n_std_dev * pd.Series(data).rolling(self.n1).std(), self.data.Close)
        self.trend_sma = self.I(SMA, self.data.Close, self.n2)

    def next(self):
        if crossover(self.data.Close, self.lower_band) and self.data.Close[-1] > self.trend_sma[-1]:
            self.buy()
            
        if crossover(self.upper_band, self.data.Close) and self.data.Close[-1] < self.trend_sma[-1]:
            self.sell()

        for trade in self.trades:
            if trade.is_long and crossover(self.sma, self.data.Close):
                self.position.close()
            elif trade.is_short and crossover(self.data.Close, self.sma):
                self.position.close()