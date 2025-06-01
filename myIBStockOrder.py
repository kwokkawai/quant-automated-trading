from termcolor import cprint
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from threading import Thread
from ibapi.contract import Contract
from ibapi.order import Order

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
        self.place_stock_order("AAPL", 10, "BUY")

    def error(self, reqId, errorCode, errorString):
        print(f"Error {reqId}: {errorCode} - {errorString}")

    def place_stock_order(self, symbol, quantity, action):
        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"
        contract.exchange = "SMART"
        contract.currency = "USD"

        order = Order()
        order.action = action  # "BUY" or "SELL"
        order.totalQuantity = quantity
        order.orderType = "MKT"

        self.placeOrder(self.next_order_id, contract, order)
        print(f"Placed {action} order for {quantity} shares of {symbol}.")

if __name__ == "__main__":
    client = IBKRClient()
    client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)
    Thread(target=client.run).start()

    import time
    # Wait for order to be placed
    time.sleep(5)
    client.disconnect()