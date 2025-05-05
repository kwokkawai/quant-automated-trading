import time
from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from threading import Thread

DEFAULT_HOST = '127.0.0.1'
DEFAULT_CLIENT_ID = 3

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

print("TRADING_PORT:", TRADING_PORT)

class IBKRPendingOrderClient(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.open_orders = []
        self.connected = False
        self._thread = Thread(target=self.run)
        self._thread.start()

    def nextValidId(self, orderId):
        self.connected = True

    def openOrder(self, orderId, contract, order, orderState):
        self.open_orders.append({
            "orderId": orderId,
            "symbol": contract.symbol,
            "action": order.action,
            "quantity": order.totalQuantity,
            "orderType": order.orderType,
            "status": orderState.status
        })

    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=None):
        print(f"IBKR Error {errorCode}: {errorString}")

def get_pending_ibkr_orders():
    client = IBKRPendingOrderClient()
    client.connect(DEFAULT_HOST, TRADING_PORT, DEFAULT_CLIENT_ID)

    if client.isConnected():
        print("Client connected to IBKR API.")

    client.reqOpenOrders()
    time.sleep(2)  # Wait for openOrder callbacks
    client.disconnect()
    client._thread.join()
    return client.open_orders

if __name__ == "__main__":

    while True:
        pending_orders = get_pending_ibkr_orders()
        print("Pending IBKR Orders:")
        for order in pending_orders:
            print(order)
        time.sleep(600)
