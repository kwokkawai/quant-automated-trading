import time
import asyncio
import os 
from websockets import connect 
import psycopg2
from psycopg2 import sql
import yfinance as yf
import datetime
from psycopg2.extras import DictCursor
from termcolor import cprint


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

    def display_portfolio(self):
        # Display the portfolio
        count = 0
        while True:
            attrs = ['bold']
            if count == 0:
                back_color = 'on_blue'
                count = 1
            else:
                back_color = 'on_white'
                count = 0
            query = sql.SQL("SELECT * FROM public.portfolio")
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            #print("\nPortfolio Summary:")
            for row in rows:
                stock_id = row['id']
                symbol = row['symbol']
                quantity = row['quantity']
                purchase_price = row['purchase_price']
                current_price = row['current_price']
                value = row['pvalue']
                gain_loss = row['gain_loss']
                last_updated = row['last_updated']
                cprint(f"{row['symbol']} {row['quantity']} {row['quantity']} {row['purchase_price']}  {row['current_price']} {row['pvalue']} {row['gain_loss']} {row['last_updated']}", 'white', back_color, attrs=attrs)

            # Wait for 60 seconds before the next iteration
            time.sleep(60)

    def close(self):
        # Close the database connection
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    # Initialize the portfolio tracker
    tracker = PortfolioTracker()

    tracker.display_portfolio()  # Display the portfolio