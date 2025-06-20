import datetime
import yfinance as yf
from yahooquery import Screener
import psycopg2
import dontshare

# PostgreSQL connection details
DB_HOST = dontshare.DB_HOST 
DB_NAME = dontshare.DB_NAME
DB_USER = dontshare.DB_USER
DB_PASSWORD = dontshare.DB_PASSWORD

# PostgreSQL connection details
DB_HOST2 = dontshare.DB_HOST2 
DB_NAME2 = dontshare.DB_NAME2
DB_USER2 = dontshare.DB_USER2
DB_PASSWORD2 = dontshare.DB_PASSWORD2

def get_data(ticker_code, start_date, end_date):

    ticker = yf.Ticker(ticker_code)
    yahoodata = ticker.history(start=start_date, end=end_date)
    selected_data = yahoodata[['Open','High','Low','Close','Volume']]
    return selected_data

def get_most_actives(count=200):
    s = Screener()
    try:
        data = s.get_screeners('most_actives', count=count)
    except Exception as e:
        print("Yahoo screener fetch failed:", e)
        data = {'most_actives': {'quotes': []}}
    return data['most_actives']['quotes']

# Save stocks data into PostgreSQL
def save_to_postgres(stocks, db_params):
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS most_actives (
            symbol TEXT PRIMARY KEY,
            shortName TEXT,
            regularMarketPrice FLOAT,
            regularMarketChange FLOAT,
            regularMarketChangePercent FLOAT,
            regularMarketVolume BIGINT,
            marketCap BIGINT
        )
    """)
    # Truncate the table before inserting new data
    cur.execute("TRUNCATE TABLE most_actives;")
    for stock in stocks:
        cur.execute("""
            INSERT INTO most_actives (symbol, shortName, regularMarketPrice, regularMarketChange, regularMarketChangePercent, regularMarketVolume, marketCap)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE SET
                shortName = EXCLUDED.shortName,
                regularMarketPrice = EXCLUDED.regularMarketPrice,
                regularMarketChange = EXCLUDED.regularMarketChange,
                regularMarketChangePercent = EXCLUDED.regularMarketChangePercent,
                regularMarketVolume = EXCLUDED.regularMarketVolume,
                marketCap = EXCLUDED.marketCap
        """, (
            stock.get('symbol'),
            stock.get('shortName'),
            stock.get('regularMarketPrice'),
            stock.get('regularMarketChange'),
            stock.get('regularMarketChangePercent'),
            stock.get('regularMarketVolume'),
            stock.get('marketCap')
        ))
    conn.commit()
    cur.close()
    conn.close()

def read_most_actives_from_db(db_params):
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, shortName, regularMarketPrice, regularMarketChange, regularMarketChangePercent, regularMarketVolume, marketCap
        FROM most_actives
    """)
    rows = cur.fetchall()
    columns = [desc[0] for desc in cur.description]
    result = [dict(zip(columns, row)) for row in rows]
    cur.close()
    conn.close()
    return result

# Example usage: fill in your PostgreSQL connection parameters
db_params = {
    'host': DB_HOST2,
    'port': 5432,
    'dbname': DB_NAME2,
    'user': DB_USER2,
    'password': DB_PASSWORD2,
}

# Get Most Active 200 Stocks
# stocks = get_most_actives(200)

# if stocks:
#     stock = stocks[0]
#     print("Stock Info:")
#     for k, v in stock.items():
#         print(f"{k:30}: {v}")
# else:
#     print("No data found.")

# save_to_postgres(stocks, db_params)

# if stocks:
#     print(
#         stocks[0]['symbol'],
#         stocks[0]['shortName'],
#         stocks[0]['regularMarketPrice'],
#         stocks[0]['regularMarketChange'],
#         stocks[0]['regularMarketChangePercent'],
#         stocks[0]['regularMarketVolume'],
#         stocks[0]['marketCap']
#     )
# else:
#     print("No data found.")


stocks = read_most_actives_from_db(db_params)

if stocks:
    stock = stocks[0]
    print("Stock Info:")
    for k, v in stock.items():
        print(f"{k:30}: {v}")
else:
    print("No data found.")

if stocks:
    print(
        stocks[0]['symbol'],
        stocks[0]['shortname'],
        stocks[0]['regularmarketprice'],
        stocks[0]['regularmarketchange'],
        stocks[0]['regularmarketchangepercent'],
        stocks[0]['regularmarketvolume'],
        stocks[0]['marketcap']
    )
else:
    print("No data found.")
