## https://openapi.futunn.com/futu-api-doc/

# from futu import OpenQuoteContext
from futu import *

# Connect to FutuOpenD (default port 11111)
quote_ctx = OpenQuoteContext(host='127.0.0.1', port=11111)

# Example: Get real-time quotes for Tencent (HK.00700)
ret, data = quote_ctx.get_market_snapshot(['HK.00700'])
if ret == 0:
    print(data)
else:
    print('Error:', data)

quote_ctx.close()

# Connect to FutuOpenD (default port 11111)
trade_ctx = OpenSecTradeContext(host='127.0.0.1', port=11111)

# Get account list
ret, data = trade_ctx.get_acc_list()
if ret == 0:
    print("Account List:")
    print(data)
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
if ret == 0:
    print(data)
    if data.shape[0] > 0:  # 如果持仓列表不为空
        print(data['stock_name'][0])  # 获取持仓第一个股票名称
        print(data['stock_name'].values.tolist())  # 转为 list
else:
    print('position_list_query error: ', data)

trade_ctx.close()
