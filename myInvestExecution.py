from termcolor import cprint
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from threading import Thread
from ibapi.contract import Contract
from ibapi.order import Order
import psycopg2
import dontshare
import time
from psycopg2 import sql

DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 1

LIVE_TRADING_PORT = 7496
PAPER_TRADING_PORT = 7497
LIVE_IB_GATEWAY_PORT = 4001
PAPER_IB_GATEWAY_PORT = 4002

LIVE_TRADING = False
IB_GATEWAY = True

if LIVE_TRADING and not IB_GATEWAY:
    TRADING_PORT = LIVE_TRADING_PORT

if not LIVE_TRADING and not IB_GATEWAY:
    TRADING_PORT = PAPER_TRADING_PORT

if LIVE_TRADING and IB_GATEWAY:
    TRADING_PORT = LIVE_IB_GATEWAY_PORT

if not LIVE_TRADING and IB_GATEWAY:
    TRADING_PORT = PAPER_IB_GATEWAY_PORT

print("TRADING_PORT:", TRADING_PORT)

class IBKRClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.next_order_id = None

    def nextValidId(self, orderId):
        print(f"Connected. Next valid order ID: {orderId}")
        self.next_order_id = orderId

        # Place an order when connection is ready
        #self.place_stock_order("AAPL", 10, "BUY")

    def error(self, reqId, errorCode, errorString):
        print(f"Error {reqId}: {errorCode} - {errorString}")

    def place_stock_order(self, symbol, quantity, action, price=None):

        print("------------ running place_stock_order")
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        order = Order()
        order.action = action  # "BUY" or "SELL"
        order.totalQuantity = quantity

        if price is not None:
            order.orderType = "LMT"
            order.lmtPrice = price
        else:
            order.orderType = "MKT"

        self.placeOrder(self.next_order_id, contract, order)

        if price is not None:
            print(f"Placed LIMIT {action} order for {quantity} shares of {symbol} at ${price}.")
        else:
            print(f"Placed MARKET {action} order for {quantity} shares of {symbol}.")

        print("------------ finish running place_stock_order")

class StockOrderExecutor:
    def __init__(self):

        print("------------ running __init__")
        # Connect to PostgreSQL
        self.dbconn = psycopg2.connect(
            host=dontshare.DB_HOST,
            database=dontshare.DB_NAME,
            user=dontshare.DB_USER,
            password=dontshare.DB_PASSWORD,
        )
        self.cursor = self.dbconn.cursor()
        print("------------ finish running __init__")

    def add_order(self, symbol, order_type, target_price, quantity):
        
        print("------------ runing add_order")
        # Add a buy/sell order to the database
        query = sql.SQL("""
            INSERT INTO public.stock_orders (symbol, order_type, target_price, quantity)
            VALUES (%s, %s, %s, %s)
        """)
        self.cursor.execute(query, (symbol, order_type, target_price, quantity))
        self.dbconn.commit()
        print(f"Added {order_type} order for {quantity} shares of {symbol} at ${target_price}. into PostgreSQL database.")
        print("------------ finish runing add_order")

    def check_and_execute_orders(self):

        print("------------ running check_and_execute_orders")
        # Fetch all pending orders
        query = sql.SQL("SELECT id, symbol, order_type, target_price, quantity FROM public.stock_orders WHERE status = 'PENDING'")
        self.cursor.execute(query)
        orders = self.cursor.fetchall()

        for order in orders:
            order_id, symbol, order_type, target_price, quantity = order

            self.ibkr_client.place_order(symbol, quantity, order_type, target_price)
            
            # Update the order status in the database
            update_query = sql.SQL("UPDATE public.stock_orders SET status = 'ORDERED' WHERE id = %s")
            self.cursor.execute(update_query, (order_id,))
            self.conn.commit()
            
            print(f"Send the {order_type} order for {symbol} at ${target_price} for {quantity}.")
        print("------------ finish running check_and_execute_orders")

    def close(self):
        print("------------ running close")
        # Close the database and IBKR connections
        self.cursor.close()
        self.conn.close()
        self.ibkr_client.disconnect()
        print("------------ finish running close")

if __name__ == "__main__":
    
    ibkr_client = IBKRClient()
    ibkr_client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    #ibkr_client.place_stock_order("AAPL", 10, "BUY",10)
    Thread(target=ibkr_client.run).start()

    # Wait for nextValidId to be set
    while ibkr_client.next_order_id is None:
        time.sleep(0.1)

    # Place a MARKET order for 10 shares of AAPL
    ibkr_client.place_stock_order("AAPL", 10, "BUY", 10)

    executor = StockOrderExecutor()
    # Example: Add buy and sell orders
    
    executor.add_order("MSFT", "SELL", 10.0, 5)  # Sell 5 shares of MSFT at $10

    # try:
    #     print("Checking PostgreSQL database for stock orders to execute...")
    #     while True:
    #         executor.check_and_execute_orders()
    #         time.sleep(60)  # Check every 60 seconds
    # except KeyboardInterrupt:
    #     print("Exiting...")
    #     executor.close()

    ibkr_client.disconnect()
