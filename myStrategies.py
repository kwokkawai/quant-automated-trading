
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
from talib import SMA
import pandas as pd
import pandas_ta as ta
import talib
from ta.momentum import StochRSIIndicator

def bands(data):
    bbands = ta.bbands(close=data.Close.s, length=20, std=2)
    return bbands.to_numpy().T

def stoch_rsi_k(data):
    stochrsi = ta.stochrsi(close=data.Close.s, k=3, d=3)
    return stochrsi['STOCHRSIk_14_14_3_3'].to_numpy()

def stoch_rsi_d(data):
    stochrsi = ta.stochrsi(close=data.Close.s, k=3, d=3)
    return stochrsi['STOCHRSId_14_14_3_3'].to_numpy()

'''
Stochrsi Strategy Overview

How the Stochrsi Strategy Works
Indicators Used:

Bollinger Bands: Measures price volatility and provides upper, middle, and lower bands.
Stochastic RSI (K and D): Measures the level of RSI relative to its range, indicating overbought or oversold conditions.
Buy Signal Logic:

The strategy checks if the current closing price is above the lower Bollinger Band.
It also checks for a crossover where the Stochastic RSI K line crosses above the D line.
If both conditions are met, it places a buy order with a stop loss (sl) at 85% of the current price and a take profit (tp) at 140% of the current price.
'''

class Stochrsi(Strategy):
    rsi_window = 14 
    stochrsi_smooth1 = 3 
    stochrsi_smooth2 = 3 
    bbands_length = 20 
    stochrsi_length = 14 
    bbands_std = 2 

    def init(self):
        self.bbands = self.I(bands, self.data)
        self.stoch_rsi_k = self.I(stoch_rsi_k, self.data)
        self.stoch_rsi_d = self.I(stoch_rsi_d, self.data)
        self.buy_price = 0 

    def next(self):
        lower = self.bbands[0] # lower bollinger band 
        mid = self.bbands[1] # middle bollinger band
        upper = self.bbands[2] # upper bollinger band

        # check for entry long positions
        if (
            self.data.Close[-1] > lower[-1] 

            and crossover(self.stoch_rsi_k, self.stoch_rsi_d)
        
        ):
            self.buy(size=0.05, sl=self.data.Close[-1] * 0.85, tp=self.data.Close[-1] * 1.40)
            self.buy_price = self.data.Close[-1]

'''
The ADXStrategy in your code is a trading strategy based on the Average Directional Index (ADX) and the Directional Indicators (+DI and -DI) from the talib library.

How the ADXStrategy Works
Indicators Used:

ADX (Average Directional Index): Measures the strength of a trend (not its direction).
+DI (Plus Directional Indicator): Indicates upward trend strength.
-DI (Minus Directional Indicator): Indicates downward trend strength.
Entry Logic:

Buy Signal:
When +DI crosses above -DI (bullish crossover) and ADX is above a threshold (default 25), indicating a strong uptrend.
Sell Signal:
When -DI crosses above +DI (bearish crossover) and ADX is above the threshold, indicating a strong downtrend.
Exit Logic:

Close Long Position:
If -DI crosses above +DI (trend reversal) or ADX drops below the exit threshold (default 20).
Close Short Position:
If +DI crosses above -DI or ADX drops below the exit threshold.
Summary Table:

Condition	Action
+DI crosses above -DI & ADX > threshold	Buy
-DI crosses above +DI & ADX > threshold	Sell
In long & (-DI crosses +DI or ADX < exit)	Close long
In short & (+DI crosses -DI or ADX < exit)	Close short
Purpose:
This strategy aims to enter trades only when a strong trend is detected and exit when the trend weakens or reverses.
'''
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

'''
Bollinger Bands Strategy Overview

The BollingerBandsStrategy is a trading strategy that uses Bollinger Bands and a trend filter to generate buy and sell signals. Here’s how it works:

How the BollingerBandsStrategy Works
Indicators Used:

Bollinger Bands: Consist of a simple moving average (SMA) and upper/lower bands set a certain number of standard deviations away from the SMA.
Trend Filter SMA: A longer-period SMA to determine the overall trend direction.
Entry Logic:

Buy Signal:
When the price crosses above the lower Bollinger Band and the price is above the trend filter SMA.
Sell Signal:
When the price crosses below the upper Bollinger Band and the price is below the trend filter SMA.
Exit Logic:

Close Long Position:
If the price crosses below the main SMA.
Close Short Position:
If the price crosses above the main SMA.
Summary Table:

Condition	Action
Price crosses above lower band & price > trend SMA	Buy
Price crosses below upper band & price < trend SMA	Sell
In long & price crosses below main SMA	Close long
In short & price crosses above main SMA	Close short
Purpose:
This strategy aims to buy when the price is low (near the lower band) in an uptrend and sell when the price is high (near the upper band) in a downtrend, using the trend filter to avoid false signals.
'''

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