import requests
import time

API_KEY = 'SYCQLXT2DD8YR3XV'

# Step 1: Get all tickers (US stocks)
url = f'https://www.alphavantage.co/query?function=LISTING_STATUS&apikey={API_KEY}'
response = requests.get(url)
lines = response.text.splitlines()
tickers = [line.split(',')[0] for line in lines[1:]]  # Skip header
print(tickers)


# Step 2: For each ticker, get latest volume (limit to first N for demo)
most_active = []
for ticker in tickers[:20]:  # Limit for demo and rate limit
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={ticker}&apikey={API_KEY}'
    r = requests.get(url)
    data = r.json()
    try:
        latest_date = list(data['Time Series (Daily)'].keys())[0]
        stock_data = data['Time Series (Daily)'][latest_date]
        print (ticker,stock_data)
        #volume = int(data['Time Series (Daily)'][latest_date]['5. volume'])
        #most_active.append((ticker, volume))
    except Exception as e:
        continue
    time.sleep(12)  # To respect free API rate limit (5 calls/min)

# # Step 3: Sort by volume
# most_active.sort(key=lambda x: x[1], reverse=True)
# print("Most active stocks (by volume):")
# for ticker, volume in most_active[:10]:
#     print(f"{ticker}: {volume}")