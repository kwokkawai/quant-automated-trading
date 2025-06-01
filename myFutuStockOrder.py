
# Update import for OpenQuoteContext
from futu import *

# Connect to FutuOpenD (make sure FutuOpenD is running on your machine)
trade_ctx = OpenSecTradeContext(host='127.0.0.1', port=11111)

# Use the simulated (paper) environment
trd_env = TrdEnv.SIMULATE

# Example: Get account list
ret, data = trade_ctx.get_acc_list()
if ret == 0:
    print(data)
    sim_acc_id = data['acc_id'][1]  # Use the first account ID
    print(sim_acc_id)
else:
    print('Error:', data)

ret, data = trade_ctx.accinfo_query()
if ret == 0:
    print(data)
    print(data['power'][0])  # 取第一行的购买力
    print(data['power'].values.tolist())  # 转为 list
else:
    print('accinfo_query error: ', data)

ret, data = trade_ctx.position_list_query()
print(ret)
print(data)

if ret == 0:
    print(data)
    if data.shape[0] > 0:  # 如果持仓列表不为空
        print(data['stock_name'][0])  # 获取持仓第一个股票名称
        print(data['stock_name'].values.tolist())  # 转为 list
else:
    print('position_list_query error: ', data)

# Example: Place a buy order (simulate environment)
order_side = TrdSide.BUY  # Buy
order_type = OrderType.NORMAL  # Normal order
#order_type = OrderType.MARKET  # Use MARKET for market order
price = 10.0  # Set your target price
qty = 100  # Number of shares
code = 'HK.00700'  # Example: Tencent stock code
acc_id = sim_acc_id   # Use your account ID from get_acc_list()

ret, order_data = trade_ctx.place_order(
    price=price,
    qty=qty,
    code=code,
    trd_side=order_side,
    order_type=order_type,
    acc_id=acc_id,
    trd_env=trd_env
)
if ret == 0:
    print('Order placed:', order_data)
else:
    print('Order error:', order_data)

# order_id = 6638639  # Replace with your actual order ID
# ret, cancel_data = trade_ctx.modify_order(
#     modify_order_op=ModifyOrderOp.CANCEL,
#     order_id=order_id,
#     qty=0,  # Not needed for cancel
#     price=0,  # Not needed for cancel
#     acc_id=sim_acc_id,
#     trd_env=trd_env
# )
# if ret == 0:
#     print('Order cancelled:', cancel_data)
# else:
#     print('Cancel order error:', cancel_data)


trade_ctx.close()
