import time
import psycopg2
from psycopg2 import sql
import yfinance as yf
import datetime
from psycopg2.extras import DictCursor
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Thread
from ib_insync import *

# PostgreSQL onnection details
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "changeme"

DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 2

LIVE_TRADING = False
IB_GATEWAY = True

LIVE_TRADING_PORT = 7496
PAPER_TRADING_PORT = 7497
LIVE_IB_GATEWAY_PORT = 4001
PAPER_IB_GATEWAY_PORT = 4002

TRADING_PORT = PAPER_TRADING_PORT

if LIVE_TRADING and not IB_GATEWAY:
    TRADING_PORT = LIVE_TRADING_PORT

if not LIVE_TRADING and not IB_GATEWAY:
    TRADING_PORT = PAPER_TRADING_PORT

if LIVE_TRADING and IB_GATEWAY:
    TRADING_PORT = LIVE_IB_GATEWAY_PORT

if not LIVE_TRADING and IB_GATEWAY:
    TRADING_PORT = PAPER_IB_GATEWAY_PORT

print("TRADING_PORT:", TRADING_PORT)

class IBKRPortfolioClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.positions = []
        self._thread = Thread(target=self.run)
        self._thread.start()

    def nextValidId(self, orderId):
        self.connected = True

    def position(self, account, contract, position, avgCost):
        # Track all instrument types, not just stocks
        # print("test")
        # print("Position.", "Account:", account, "Contract:", contract, "Position:", position, "Avg cost:", avgCost)
        print(f"Received position: account={account}, symbol={contract.symbol}, secType={contract.secType}, position={position}, avgCost={avgCost}")
        self.positions.append({
            "symbol": contract.symbol,
            "secType": contract.secType,
            "exchange": contract.exchange,
            "currency": contract.currency,
            "position": position,
            "avg_cost": avgCost
        })

    def positionEnd(self):
        print("All positions received from IBKR.")
        self.disconnect()

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        print(f"IBKR Error {errorCode}: {errorString}")

def sync_ibkr_portfolio_to_local(tracker):
    # Retrieve portfolio from IBKR
    ibkr_client = IBKRPortfolioClient()
    ibkr_client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)

    # Wait for connection
    timeout = 10
    waited = 0
    while not ibkr_client.isConnected and waited < timeout:
        time.sleep(0.1)
        waited += 0.1
    if not ibkr_client.isConnected:
        print("Could not connect to IBKR API.")
        return

    ibkr_client.reqPositions()
    time.sleep(2)
    ibkr_client._thread.join()
    
    # ibkr_client.reqPositionsMulti(2, "DU7562575", "")   
    # Wait a bit to ensure data is received
    # time.sleep(1)
    # ibkr_client._thread.start()

    print("Positions received from IBKR:", ibkr_client.positions)

    # Update local portfolio table
    for pos in ibkr_client.positions:
        symbol = pos["symbol"]
        quantity = int(pos["quantity"])
        avg_cost = float(pos["avg_cost"])

        # Check if the symbol already exists
        tracker.cursor.execute("SELECT id FROM public.portfolio WHERE symbol = %s", (symbol,))
        result = tracker.cursor.fetchone()
        if result:
            # Update existing record
            tracker.cursor.execute(
                "UPDATE public.portfolio SET quantity = %s, purchase_price = %s WHERE symbol = %s",
                (quantity, avg_cost, symbol)
            )
        else:
            # Insert new record
            tracker.cursor.execute(
                "INSERT INTO public.portfolio (symbol, quantity, purchase_price) VALUES (%s, %s, %s)",
                (symbol, quantity, avg_cost)
            )
        tracker.conn.commit()
    
    print("Local portfolio table updated from IBKR positions.")

class PortfolioTracker:
    def __init__(self):
        # Connect to PostgreSQL
        self.conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=DictCursor
        )
        self.cursor = self.conn.cursor()

    def add_stock(self, symbol, quantity, purchase_price):
        # Add a stock to the portfolio
        query = sql.SQL("""
            INSERT INTO public.portfolio (symbol, quantity, purchase_price)
            VALUES (%s, %s, %s)
        """)
        self.cursor.execute(query, (symbol, quantity, purchase_price))
        self.conn.commit()
        print(f"Added {quantity} shares of {symbol} at ${purchase_price} each.")

    def remove_stock(self, symbol):
        # Remove a stock from the portfolio
        query = sql.SQL("DELETE FROM public.portfolio WHERE symbol = %s")
        self.cursor.execute(query, (symbol,))
        self.conn.commit()
        print(f"Removed {symbol} from the portfolio.")

    def fetch_prices(self):
        # Fetch current prices for all stocks in the portfolio
        query = sql.SQL("SELECT id, symbol, quantity, purchase_price FROM public.portfolio")
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        for row in rows:
            stock_id, symbol, quantity, purchase_price = row
            stock = yf.Ticker(symbol)
            current_price = float(stock.history(period="1d")["Close"].iloc[-1])  # Ensure current_price is a float
            value = quantity * current_price
            gain_loss = (current_price - float(purchase_price)) * quantity  # Convert purchase_price to float

            # Update the database with the current price, value, and gain/loss
            update_query = sql.SQL("""
                UPDATE public.portfolio
                SET current_price = %s, pvalue = %s, gain_loss = %s, last_updated = %s
                WHERE id = %s
            """)
            self.cursor.execute(update_query, (current_price, value, gain_loss, datetime.datetime.now(), stock_id))
            self.conn.commit()

    def display_portfolio(self):
        # Display the portfolio
        query = sql.SQL("SELECT * FROM public.portfolio")
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        print("\nPortfolio Summary:")
        for row in rows:
            stock_id = row['id']
            symbol = row['symbol']
            quantity = row['quantity']
            purchase_price = row['purchase_price']
            current_price = row['current_price']
            value = row['pvalue']
            gain_loss = row['gain_loss']
            last_updated = row['last_updated']

            print(f"ID: {stock_id}, Symbol: {symbol}, Quantity: {quantity}, "
                f"Purchase Price: {purchase_price}, Current Price: {current_price}, "
                f"Value: {value}, Gain/Loss: {gain_loss}, Last Updated: {last_updated}")

    def close(self):
        # Close the database connection
        self.cursor.close()
        self.conn.close()

def getPosition():
    ib = IB()

    ib.connect(DEFAULT_HOST, TRADING_PORT, clientId=DEFAULT_CLIENT_ID)
    position_list = ib.positions()
    #print(position_list)
    for position in position_list:
        print(f"Account: {position.account}, Symbol: {position.contract.symbol}, Currency: {position.contract.currency}, position: {position.position}, avgCost: {position.avgCost}")
        symbol = position.contract.symbol
        quantity = int(position.position)
        avg_cost = float(position.avgCost)

        # Check if the symbol already exists
        tracker.cursor.execute("SELECT id FROM public.portfolio WHERE symbol = %s", (symbol,))
        result = tracker.cursor.fetchone()
        if result:
            # Update existing record
            tracker.cursor.execute(
                "UPDATE public.portfolio SET quantity = %s, purchase_price = %s WHERE symbol = %s",
                (quantity, avg_cost, symbol)
            )
        else:
            # Insert new record
            tracker.cursor.execute(
                "INSERT INTO public.portfolio (symbol, quantity, purchase_price) VALUES (%s, %s, %s)",
                (symbol, quantity, avg_cost)
            )
        tracker.conn.commit()


if __name__ == "__main__":

    while True:
    #Initialize the portfolio tracker
        tracker = PortfolioTracker()
        getPosition()
        # Fetch current prices and update the database
        tracker.fetch_prices() 
        time.sleep(600)

    # Example usage
    #tracker.add_stock("AAPL", 10, 150)  # Add 10 shares of AAPL purchased at $150 each
    #tracker.add_stock("MSFT", 5, 300)  # Add 5 shares of MSFT purchased at $300 each
    # while True:
    #     # Sync portfolio from IBKR to local DB
    #     sync_ibkr_portfolio_to_local(tracker)

    #     # Fetch current prices and update the database
    #     tracker.fetch_prices() 
    #     time.sleep(600)

    #tracker.display_portfolio()  # Display the portfolio