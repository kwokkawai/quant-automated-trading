import datetime
import yfinance as yf
from yahooquery import Screener
import psycopg2

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
            shortname TEXT,
            regularMarketPrice FLOAT,
            regularMarketChange FLOAT,
            regularMarketChangePercent FLOAT,
            regularMarketVolume BIGINT,
            marketCap BIGINT
        )
    """)
    for stock in stocks:
        cur.execute("""
            INSERT INTO most_actives (symbol, shortname, regularMarketPrice, regularMarketChange, regularMarketChangePercent, regularMarketVolume, marketCap)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol) DO UPDATE SET
                shortname = EXCLUDED.shortname,
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

def read_most_actives(db_params):
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, shortname, regularMarketPrice, regularMarketChange, regularMarketChangePercent, regularMarketVolume, marketCap
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
    'host': 'localhost',
    'port': 5432,
    'dbname': 'postgres',
    'user': 'pkwok',
    'password': 'GW123456'
}

# stocks = get_most_actives()

# if stocks:
#     save_to_postgres(stocks, db_params)

stocks = read_most_actives(db_params)

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

