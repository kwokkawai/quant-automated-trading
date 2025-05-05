import time
import psycopg2
from psycopg2 import sql
import yfinance as yf
import datetime
from psycopg2.extras import DictCursor

# PostgreSQL connection details
DB_HOST = "localhost"
DB_NAME = "postgres"
DB_USER = "postgres"
DB_PASSWORD = "changeme"

class PortfolioTracker:
    def __init__(self):
        # Connect to PostgreSQL
        self.conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            cursor_factory=DictCursor
        )
        self.cursor = self.conn.cursor()

    def add_stock(self, symbol, quantity, purchase_price):
        # Add a stock to the portfolio
        query = sql.SQL("""
            INSERT INTO public.portfolio (symbol, quantity, purchase_price)
            VALUES (%s, %s, %s)
        """)
        self.cursor.execute(query, (symbol, quantity, purchase_price))
        self.conn.commit()
        print(f"Added {quantity} shares of {symbol} at ${purchase_price} each.")

    def remove_stock(self, symbol):
        # Remove a stock from the portfolio
        query = sql.SQL("DELETE FROM public.portfolio WHERE symbol = %s")
        self.cursor.execute(query, (symbol,))
        self.conn.commit()
        print(f"Removed {symbol} from the portfolio.")

    def fetch_prices(self):
        # Fetch current prices for all stocks in the portfolio
        query = sql.SQL("SELECT id, symbol, quantity, purchase_price FROM public.portfolio")
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        for row in rows:
            stock_id, symbol, quantity, purchase_price = row
            stock = yf.Ticker(symbol)
            current_price = float(stock.history(period="1d")["Close"].iloc[-1])  # Ensure current_price is a float
            value = quantity * current_price
            gain_loss = (current_price - float(purchase_price)) * quantity  # Convert purchase_price to float

            # Update the database with the current price, value, and gain/loss
            update_query = sql.SQL("""
                UPDATE public.portfolio
                SET current_price = %s, pvalue = %s, gain_loss = %s, last_updated = %s
                WHERE id = %s
            """)
            self.cursor.execute(update_query, (current_price, value, gain_loss, datetime.datetime.now(), stock_id))
            self.conn.commit()

    def display_portfolio(self):
        # Display the portfolio
        query = sql.SQL("SELECT * FROM public.portfolio")
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        print("\nPortfolio Summary:")
        for row in rows:
            stock_id = row['id']
            symbol = row['symbol']
            quantity = row['quantity']
            purchase_price = row['purchase_price']
            current_price = row['current_price']
            value = row['pvalue']
            gain_loss = row['gain_loss']
            last_updated = row['last_updated']

            print(f"ID: {stock_id}, Symbol: {symbol}, Quantity: {quantity}, "
                f"Purchase Price: {purchase_price}, Current Price: {current_price}, "
                f"Value: {value}, Gain/Loss: {gain_loss}, Last Updated: {last_updated}")

    def close(self):
        # Close the database connection
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    # Initialize the portfolio tracker
    tracker = PortfolioTracker()

    # Example usage
    #tracker.add_stock("AAPL", 10, 150)  # Add 10 shares of AAPL purchased at $150 each
    #tracker.add_stock("MSFT", 5, 300)  # Add 5 shares of MSFT purchased at $300 each

    tracker.fetch_prices()  # Fetch current prices and update the database
    tracker.display_portfolio()  # Display the portfolio