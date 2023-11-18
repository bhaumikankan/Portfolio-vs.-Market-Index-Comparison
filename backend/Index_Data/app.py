import time
import pandas as pd
import yfinance as yf
import requests

# Function to fetch stock data for a single symbol
def fetch_stock_data(symbol):
    try:
        stock_data = yf.download(symbol, start="2013-10-18", end="2023-10-18")
        return stock_data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return None

# Read symbols from an Excel file
symbols_df = pd.read_excel('symbols.xlsx')
symbols = symbols_df['StockSymbol'].tolist()

# Define rate limit settings
stocks_per_hour_limit = 900
pause_time = 3600 / stocks_per_hour_limit  # Pause for one hour

# Initialize variables for tracking
current_batch = 0

# Main loop to fetch and save stock data
for symbol in symbols:
    stock_data = fetch_stock_data(symbol)
    if stock_data is not None:
        # Save data to Excel and JSON
        stock_data.to_excel(f'{symbol}_data.xlsx')
        stock_data.to_json(f'{symbol}_data.json')
        current_batch += 1

    # Implement rate limiting
    if current_batch >= stocks_per_hour_limit:
        print(f"Pausing for {pause_time} seconds...")
        time.sleep(pause_time)
        current_batch = 0

# You can continue the loop for remaining symbols here
# ...

print("Data retrieval and saving complete.")
