## This program is to run backtesting on multiple strategies and multiple stocks from a CSV file and 200 top US stocks from Yahoo Finance screener
## Result will be saved to PostgreSQL database

import datetime
import yfinance as yf
from backtesting import Backtest
from myStrategies import ADXStrategy, BollingerBandsStrategy  # Import strategies
import threading
import csv
from termcolor import cprint
from yahooquery import Screener
import time

import psycopg2

# PostgreSQL connection details
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "changeme"

# Map strategy class names to actual classes
strategy_classes = {
    "ADXStrategy": ADXStrategy,
    "BollingerBandsStrategy": BollingerBandsStrategy
}

def get_data(ticker_code, start_date, end_date):

    ticker = yf.Ticker(ticker_code)
    yahoodata = ticker.history(start=start_date, end=end_date)
    selected_data = yahoodata[['Open','High','Low','Close','Volume']]
    return selected_data


def get_next_batch_id(db_params):
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(batch_id) FROM public.backtest_results")
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result and result[0] is not None:
        return int(result[0]) + 1
    else:
        return 1


def run_backtest(ticker_code,start_date,end_date, strategy_class, doPlot,batch_id):
    bt = Backtest(get_data(ticker_code,start_date,end_date), strategy_class, cash=1000000, commission=.002)
    #bt = Backtest(get_data(ticker_code), ADXStrategy , cash=1000000, commission=.002, margin=1.0)
    try:
        stats = bt.run()
    except Exception as e:
        return
    
    #print(stats)
    #print(f"{ticker_code} Sharpe Ratio is {stats['Sharpe Ratio']} using strategy: {strategy_class.__name__}")
    #print(f"{ticker_code} Sortino Ratio is {stats['Sortino Ratio']} using strategy: {strategy_class.__name__}")
    
    if stats['Sharpe Ratio'] > 1 or stats['Sortino Ratio'] > 1.5:
        # output = f"{ticker_code} using strategy: {strategy_class.__name__} Sharpe Ratio is {stats['Sharpe Ratio']}"
        # cprint(output, 'white', f'on_red', attrs=['bold'])
        # output = f"{ticker_code} using strategy: {strategy_class.__name__} Sortino Ratio is {stats['Sortino Ratio']}"
        # cprint(output, 'white', f'on_blue', attrs=['bold'])

        # In your run_backtest function, after stats = bt.run():
        db_params = {
            'host': DB_HOST,
            'database': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD
        }
        save_backtest_stats_to_db(
            stats,
            ticker_code,
            strategy_class.__name__,
            start_date,
            end_date,
            db_params,
            batch_id
        )

    else:
        # output = f"{ticker_code} using strategy: {strategy_class.__name__} Sharpe Ratio is {stats['Sharpe Ratio']}"
        # cprint(output, 'white', f'on_grey', attrs=['bold'])
        # output = f"{ticker_code} using strategy: {strategy_class.__name__} Sortino Ratio is {stats['Sortino Ratio']}"
        # cprint(output, 'white', f'on_grey', attrs=['bold'])
        pass

    if doPlot == 1:
        # Save the plot to a file instead of displaying it
        plot_filename = f"{ticker_code}_{strategy_class.__name__}_plot.html"
        bt.plot(filename=plot_filename)
        print(f"Plot saved to {plot_filename}")

def save_backtest_stats_to_db(stats, ticker_code, strategy_class, start_date, end_date, db_params,batch_id):
    conn = psycopg2.connect(**db_params)
    cursor = conn.cursor()
    insert_query = """
        INSERT INTO public.backtest_results (
            batch_id,ticker_code, strategy_class, start_date, end_date,
            sharpe_ratio, sortino_ratio, total_return, buy_hold_return,
            annual_return, annual_volatility, calmar_ratio, max_drawdown, avg_drawdown,
            max_drawdown_duration, avg_drawdown_duration, trades, win_rate,
            best_trade, worst_trade, avg_trade, max_trade_duration, avg_trade_duration,
            profit_factor, expectancy, sqn, equity_final, equity_peak, exposure_time
        ) VALUES (
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
    """
    values = (
        batch_id,
        ticker_code,
        strategy_class,
        start_date,
        end_date,
        stats.get('Sharpe Ratio'),
        stats.get('Sortino Ratio'),
        stats.get('Return [%]'),
        stats.get('Buy & Hold Return [%]'),
        stats.get('Return (Ann.) [%]'),
        stats.get('Volatility (Ann.) [%]'),
        stats.get('Calmar Ratio'),
        stats.get('Max. Drawdown [%]'),
        stats.get('Avg. Drawdown [%]'),
        stats.get('Max. Drawdown Duration'),
        stats.get('Avg. Drawdown Duration'),
        stats.get('# Trades'),
        stats.get('Win Rate [%]'),
        stats.get('Best Trade [%]'),
        stats.get('Worst Trade [%]'),
        stats.get('Avg. Trade [%]'),
        stats.get('Max. Trade Duration'),
        stats.get('Avg. Trade Duration'),
        stats.get('Profit Factor'),
        stats.get('Expectancy [%]'),
        stats.get('SQN'),
        stats.get('Equity Final [$]'),
        stats.get('Equity Peak [$]'),
        stats.get('Exposure Time [%]')
    )
    cursor.execute(insert_query, values)
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":

    while True:

        # Before starting your batch of backtests:
        db_params = {
            'host': DB_HOST,
            'database': DB_NAME,
            'user': DB_USER,
            'password': DB_PASSWORD
        }
        batch_id = get_next_batch_id(db_params)

        # # Read input from a CSV file and create threads dynamically
        threads = []
        # Use Yahoo Finance screener to fetch US stocks
        s = Screener()
        try:
            data = s.get_screeners('most_actives', count=200)
        except Exception as e:
            print("Yahoo screener fetch failed:", e)
            data = {'most_actives': {'quotes': []}}
        
        stocks = data['most_actives']['quotes']

        for stock in stocks:
            #print(stock['symbol'])
            ticker_code = stock['symbol']
            start_date = datetime.datetime.strptime('2023-01-01', '%Y-%m-%d')
            end_date = datetime.datetime.now().date()
            doPlot = 0

            # Create a thread for each row in the input file for 1 strategy
            # strategy_class = strategy_classes['BollingerBandsStrategy']
            # thread = threading.Thread(target=run_backtest, args=(ticker_code, start_date, end_date, strategy_class, doPlot,batch_id))
            # threads.append(thread)

            # Loop through all strategies
            for strategy_class in strategy_classes.values():
                thread = threading.Thread(
                    target=run_backtest,
                    args=(ticker_code, start_date, end_date, strategy_class, doPlot, batch_id)
                )
                threads.append(thread)

        with open('/Users/pkwok/Projects/20. Algo/stock/myModels.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                ticker_code = row['ticker_code']
                start_date = datetime.datetime.strptime(row['start_date'], '%Y-%m-%d')
                if row['end_date'] == 'now':
                    end_date = datetime.datetime.now().date()
                else:
                    end_date = datetime.datetime.strptime(row['end_date'], '%Y-%m-%d')
                strategy_class = strategy_classes[row['strategy_class']]
                doPlot = int(row['doPlot'])
                
                # Create a thread for each row in the input file for 1 strategy
                # thread = threading.Thread(target=run_backtest, args=(ticker_code, start_date, end_date, strategy_class, doPlot,batch_id))
                # threads.append(thread)

                # Loop through all strategies
                for strategy_class in strategy_classes.values():
                    thread = threading.Thread(
                        target=run_backtest,
                        args=(ticker_code, start_date, end_date, strategy_class, doPlot, batch_id)
                    )
                    threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        print("Running Backtest at", datetime.datetime.now().date())
        time.sleep(60*60*24)  # Check every 1 Day