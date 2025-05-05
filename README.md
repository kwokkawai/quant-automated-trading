
# Quant Automated Trading Project

This project is a comprehensive framework for **quantitative automated trading** using Python. It integrates data collection, backtesting, order execution, and portfolio tracking, with a focus on automation and extensibility. My target is to automate ALL my investment strategy only based on the Quant Automated Trading

## Project Structure

### 1. **Backtesting**
- **myBacktesting.py**  
  Runs backtests on multiple stocks and strategies in parallel using threading. Results are saved to a PostgreSQL database with batch tracking. Supports both Yahoo screener and custom CSV input.
- **myStrategies.py**  
  Contains custom trading strategies (e.g., ADXStrategy, BollingerBandsStrategy) compatible with the [backtesting.py](https://kernc.github.io/backtesting.py/) library.
- **myPGtables.sql**  
  SQL scripts to create and manage PostgreSQL tables for storing backtest results and portfolio data.

### 2. **Order Execution**
- **myStockOrder.py**  
  Monitors pending orders in a PostgreSQL table, checks market prices, and places orders via the Interactive Brokers (IBKR) API when conditions are met. Supports both live and paper trading, and updates order status in the database.

- **myIBKRpendingOrder.py**  
  Retrieves and displays all pending (open) orders from IBKR using the API, useful for monitoring and reconciliation.

### 3. **Portfolio Tracking**
- **myPortfolioTracker.py**  
  Syncs portfolio positions from IBKR to the local PostgreSQL database, updates prices, and displays portfolio performance.

### 4. **Utilities & Data**
- **myModels.csv**  
  CSV file for batch backtesting, specifying tickers, date ranges, and strategies.
- **save_backtest_results.py**  
  Utility for saving backtest statistics to the database.

### 5. **Documentation**
- **README.md**  
  Project overview and usage instructions.

---

## Key Features

- **Automated Backtesting:**  
  Batch backtesting for multiple stocks and strategies, with results stored in a structured database for analysis.

- **Order Management:**  
  Automated order placement and status tracking with IBKR, including support for both live and paper trading environments.

- **Portfolio Synchronization:**  
  Keeps your local portfolio database in sync with your IBKR account.

- **Extensible Design:**  
  Easily add new strategies, data sources, or broker integrations.

---

## Requirements

- Python 3.8+
- [backtesting.py](https://kernc.github.io/backtesting.py/)
- [ibapi](https://interactivebrokers.github.io/)
- [psycopg2](https://www.psycopg.org/)
- [yahooquery](https://github.com/dpguthrie/yahooquery)
- [termcolor](https://pypi.org/project/termcolor/)
- PostgreSQL

---

## Getting Started

1. **Set up PostgreSQL** using the provided SQL scripts.
2. **Configure IBKR API** (TWS or IB Gateway) for order execution and portfolio sync.
3. **Edit `myModels.csv`** or use Yahoo screener for batch backtesting.
4. **Run backtests:**  
   ```bash
   python myBacktesting.py
   ```
5. **Monitor and execute orders:**  
   ```bash
   python myStockOrder.py
   ```
6. **Sync and view portfolio:**  
   ```bash
   python myPortfolioTracker.py
   ```

---

## Disclaimer

This project is for educational and research purposes only. Use at your own risk. Automated trading involves significant risk of loss.
