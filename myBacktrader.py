
import datetime 
import backtrader as bt 
import backtrader.analyzers as btanalyzers
import yfinance as yf

ticker_code = "SAP"
start_date = datetime.datetime(2023, 4, 26)
end_date = datetime.datetime(2025, 4, 26)

def get_data(ticker_code):

    ticker = yf.Ticker(ticker_code)
    yahoodata = ticker.history(start=start_date, end=end_date)
    # Add a new column 'Adj Close' and set it equal to 'Close'
    yahoodata['Adj Close'] = yahoodata['Close']
    selected_data = yahoodata[['Open','High','Low','Close','Adj Close','Volume']]
    #selected_data = data[['Open','High','Low','Close','Adj Close','Volume']]
    selected_data.to_csv("/Users/pkwok/Projects/20. Algo/ATC Bootcamp Code 2025/Data/" + ticker_code + ".csv", index=True)
    #print(selected_data.to_string())

# THIS IS WHERE WE DEFINE OUR STRATEGY
class SmaCross(bt.SignalStrategy):
    def __init__(self): 
        # when simple moving average crosses the price, can change the number
        sma = bt.ind.SMA(period=20)
        # this grabs the price data from the excel
        price = self.data
        # this defines the cross over.. price and sma
        crossover = bt.ind.CrossOver(price, sma)
        # this tells the code to LONG when it crossover, which is defined above
        self.signal_add(bt.SIGNAL_LONG, crossover)


def cerebro_process():
    # this is activating the engine
    cerebro = bt.Cerebro()
    # this adds the strategy to it
    cerebro.addstrategy(SmaCross)

    # this is pulling data from yahoo fin but doesnt work well, so i used larrys below
    # data = bt.feeds.YahooFinanceData(dataname = "BTC-USD", fromdate=datetime(2015, 1, 1),
    #         todate=datetime(2022, 1, 1))

    # this is how i use manually pulled data from yahoo finance, prob the one i use for now
    data = bt.feeds.YahooFinanceCSVData(

        dataname = '/Users/pkwok/Projects/20. Algo/ATC Bootcamp Code 2025/Data/' + ticker_code + '.csv',
    
        # do not pass values before this date
        # this is when we want to start the date
        fromdate = start_date,
        # do not passs values after this date
        todate = end_date,
        reverse = False
    )

    # this sets the cash amount to the back test
    cerebro.broker.set_cash(1000000)

    # set the commision 0.1% ... divide by 100 to remove the %
    # phemex contract is .00075 taker and -.00025 for maker
    # phemex spot is .001 for taker & maker
    # ftx is .001 for maker and .004 for taker
    cerebro.broker.setcommission(commission=0.001)

    # this adds the data to the cerebro engine
    cerebro.adddata(data)

    # this says go all in, well 95% so we dont miss
    cerebro.addsizer(bt.sizers.AllInSizer, percents=95)

    # now adding some analyzers...
    # this one beelow is how we get the sharpe analyzer
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name = 'sharpe')
    # this is the transactions analyzer
    cerebro.addanalyzer(btanalyzers.Transactions, _name = 'tx')
    # this is the trade analyzer
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name = 'trades')

    cerebro.run()

    # now we run our engine & add it to a variable so we can later check perf
    back = cerebro.run() 

    # this gets our value back 
    endvalue = cerebro.broker.getvalue() 

    # below we are looking at our 3 analyzers.. sharpe here
    sharpe = back[0].analyzers.sharpe.get_analysis() 


    # this is running out transaction analyzer
    txs = back[0].analyzers.tx.get_analysis() 

    # this is running our trades analzer
    trades = back[0].analyzers.trades.get_analysis() 

    #print(txs)

    txamount = len(txs)

    # The Sharpe Ratio is a financial metric used to evaluate the performance of an investment by adjusting for its risk. It measures the return of an investment compared to its risk, helping investors understand whether the returns are due to smart investment decisions or excessive risk.
    # Formula:
    # The Sharpe Ratio is calculated as:
    # Sharpe Ratio = (Return of the Portfolio - Risk-Free Rate) / Standard Deviation of the Portfolio's Excess Return

    #print(f"ending value is {endvalue}")
    print(f"sharpe ratio is {sharpe} and this many txs: {txamount} final value {cerebro.broker.getvalue()}")
    #print(f"transactions are {txs}")
    #print(f"trades are {trades}")

    # this shows the final portfolio value
    #print("final protfolio value: %.2f" % cerebro.broker.getvalue())

    # this plots the backtest
    cerebro.plot()

get_data(ticker_code)
cerebro_process()
