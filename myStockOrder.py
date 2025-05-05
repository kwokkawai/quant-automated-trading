import time
import psycopg2
from psycopg2 import sql
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Thread
import yfinance as yf
from termcolor import cprint
from ibapi.order import Order

# PostgreSQL connection details
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "changeme"

DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1

LIVE_TRADING_PORT = 7496
PAPER_TRADING_PORT = 7497
LIVE_IB_GATEWAY_PORT = 4001
PAPER_IB_GATEWAY_PORT = 4002

LIVE_TRADING = False
IB_GATEWAY = True

TRADING_PORT = PAPER_TRADING_PORT

if LIVE_TRADING and not IB_GATEWAY:
    TRADING_PORT = LIVE_TRADING_PORT

if not LIVE_TRADING and not IB_GATEWAY:
    TRADING_PORT = PAPER_TRADING_PORT

if LIVE_TRADING and IB_GATEWAY:
    TRADING_PORT = LIVE_IB_GATEWAY_PORT

if not LIVE_TRADING and IB_GATEWAY:
    TRADING_PORT = PAPER_IB_GATEWAY_PORT

class IBKRClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.order_executed = False

    def error(self, req_id, code, msg, misc):
        print(f"Error {req_id}: {code} - {msg}")

    def nextValidId(self, order_id):
        self.next_order_id = order_id

    def orderStatus(self, order_id, status, filled, remaining, avg_fill_price, perm_id, parent_id, last_fill_price, client_id, why_held, mkt_cap_price):
        print(f"Order Status. ID: {order_id}, Status: {status}")
        if status == "Filled":
            self.order_executed = True

    def place_order(self, symbol, quantity, action):
        # Define the contract for the stock
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"  # Stock
        contract.exchange = "SMART"
        contract.currency = "USD"

        # Define the order
        order = Order()
        order.action = action  # 'BUY' or 'SELL'
        order.totalQuantity = quantity
        order.orderType = "MKT"  # Market order
        order.outsideRth = True 

        # Place the order
        self.placeOrder(self.next_order_id, contract, order)
        print(f"Placed {action} order for {quantity} shares of {symbol}.")

class StockOrderExecutor:
    def __init__(self):
        # Connect to PostgreSQL
        self.conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        self.cursor = self.conn.cursor()

        # Initialize IBKR client
        self.ibkr_client = IBKRClient()
        self.ibkr_client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
        thread = Thread(target=self.ibkr_client.run)
        thread.start()

    def add_order(self, symbol, order_type, target_price, quantity):
        # Add a buy/sell order to the database
        query = sql.SQL("""
            INSERT INTO public.stock_orders (symbol, order_type, target_price, quantity)
            VALUES (%s, %s, %s, %s)
        """)
        self.cursor.execute(query, (symbol, order_type, target_price, quantity))
        self.conn.commit()
        print(f"Added {order_type} order for {quantity} shares of {symbol} at ${target_price}.")

    def check_and_execute_orders(self):
        # Fetch all pending orders
        query = sql.SQL("SELECT id, symbol, order_type, target_price, quantity FROM public.stock_orders WHERE status = 'PENDING'")
        self.cursor.execute(query)
        orders = self.cursor.fetchall()

        for order in orders:
            order_id, symbol, order_type, target_price, quantity = order

            # Fetch the current stock price
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d")["Close"].iloc[-1]

            attrs = ['bold']
            font_color = 'white'
            back_color = 'on_grey'
            #print(f"Checking {order_type} order for {symbol}: Target ${target_price}, Current ${current_price}")
            cprint(f"Checking {order_type} order for {symbol}: Target ${target_price}, Current ${current_price}", font_color, back_color, attrs=attrs)                    

            # Check if the target price is hit
            if (order_type == "BUY" and current_price <= target_price) or (order_type == "SELL" and current_price >= target_price):
                # Trigger the order execution
                self.ibkr_client.place_order(symbol, quantity, order_type)

                # Update the order status in the database
                update_query = sql.SQL("UPDATE public.stock_orders SET status = 'ORDERED' WHERE id = %s")
                self.cursor.execute(update_query, (order_id,))
                self.conn.commit()
                #print(f"Executed {order_type} order for {symbol} at ${current_price}.")
                attrs = ['bold']
                font_color = 'white'
                if order_type == "BUY":
                    back_color = 'on_green'
                else:
                    back_color = 'on_yellow'
                cprint(f"Executed {order_type} order for {symbol} at ${current_price}.", font_color, back_color, attrs=attrs)

    def close(self):
        # Close the database and IBKR connections
        self.cursor.close()
        self.conn.close()
        self.ibkr_client.disconnect()

if __name__ == "__main__":
    executor = StockOrderExecutor()

    # Example: Add buy and sell orders
    #executor.add_order("AAPL", "BUY", 206.0, 10)  # Buy 10 shares of AAPL at $150
    #executor.add_order("MSFT", "SELL", 300.0, 5)  # Sell 5 shares of MSFT at $300

    try:
        while True:
            executor.check_and_execute_orders()
            time.sleep(60)  # Check every 60 seconds
    except KeyboardInterrupt:
        print("Exiting...")
        executor.close()