from yahooquery import Screener

# Use Yahoo Finance screener to fetch US stocks
s = Screener()
data = s.get_screeners('most_actives', count=200)  # Fetch most active US stocks
stocks = data['most_actives']['quotes']

for stock in stocks:
    print(stock['symbol'])

# Extract ticker symbols
#tickers = [stock['symbol'] for stock in stocks]
#print(tickers)