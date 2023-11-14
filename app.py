import csv

import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64
from fastapi import FastAPI, File, UploadFile

app = FastAPI()

def get_stock_data_from_file(ticker, start_date, end_date):
    file_path = f"Stock_Data/{ticker}_data.xlsx"
    stock_data = pd.read_excel(file_path, parse_dates=True, index_col='Date')
    stock_data = stock_data[start_date:end_date]
    return stock_data

def get_index_data_from_file(index_ticker, start_date, end_date):
    file_path = f"Index_Data/{index_ticker}_data.xlsx"
    index_data = pd.read_excel(file_path, parse_dates=True, index_col='Date')
    index_data = index_data[start_date:end_date]
    return index_data

def create_portfolio(stocks, tickers, quantities, betas):
    portfolio = pd.DataFrame()
    portfolio_value = 0
    portfolio_weighted_beta = 0
    total_quantity = 0

    for stock, ticker, quantity, beta in zip(stocks, tickers, quantities, betas):
        portfolio[ticker] = stock['Close']
        total_quantity += quantity
        portfolio_value += stock['Close'].iloc[-1] * quantity
        portfolio_weighted_beta += beta * quantity

    if total_quantity != 0:
        portfolio_weighted_beta /= total_quantity  # Calculate the weighted beta

    return portfolio, portfolio_value, portfolio_weighted_beta

def plot_price_relation(portfolio, index_data, portfolio_name, index_name):
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.set_xlabel('Date')
    ax1.set_ylabel(f'{portfolio_name} Portfolio', color='tab:blue')
    ax1.plot(portfolio.index, portfolio.sum(axis=1) / portfolio.sum(axis=1).iloc[0], color='tab:blue', label=portfolio_name)
    ax1.tick_params(axis='y', labelcolor='tab:blue')

    ax2 = ax1.twinx()
    ax2.set_ylabel(f'{index_name} Normalized Closing Price', color='tab:red')
    ax2.plot(index_data.index, index_data['Close'] / index_data['Close'].iloc[0], color='tab:red', label=index_name)
    ax2.tick_params(axis='y', labelcolor='tab:red')

    plt.title('Percentage Correlation Chart')
    plt.legend(loc='upper left')

    correlation = portfolio.sum(axis=1).corr(index_data['Close'])

    plt.text(
        portfolio.index[10], 1.05, f'Correlation: {correlation:.2f}', fontsize=12, color='tab:blue')

    # Interpretation of the correlation result
    correlation_meaning = ""
    if correlation > 0.7:
        correlation_meaning = "Strong positive correlation (Same direction) Short Underlying Index to Hedge"
    elif correlation < -0.7:
        correlation_meaning = "Strong negative correlation (Opposite direction) Long Underlying Index to Hedge"
    elif correlation >= 0.25:
        correlation_meaning = "Moderate positive correlation (Same direction) Consult With Registered Advisor to Hedge"
    elif correlation <= -0.25:
        correlation_meaning = "Moderate negative correlation (Opposite direction) Long Underlying Index to Hedge"
    elif correlation >= 0.1 or correlation <= -0.1:
        correlation_meaning = "Low correlation Consult With Registered Advisor to Hedge"
    else:
        correlation_meaning = "No significant correlation Consult With Registered Advisor to Hedge"

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode(), correlation, correlation_meaning

def csv_to_dict(csv_content):
    # Assuming the CSV has a header row
    reader = csv.DictReader(csv_content.splitlines())
    rows = list(reader)
    return rows

@app.post("/")
async def ratio_analyser(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        csv_data = contents.decode()

        # Convert CSV data to a list of dictionaries
        input_data = csv_to_dict(csv_data)


        portfolio_stocks = []
        portfolio_tickers = []
        portfolio_betas = []
        portfolio_quantities = []
        portfolio_stock_data = {}  # To store stock name and quantity

        #num_portfolio_stocks = int(input("Enter the number of stocks in your portfolio: "))
        for d in input_data:
            stock_ticker = f"{d['symbol']}.NS" #input(f"Enter stock symbol {i + 1}: ")
            start_date = "-".join(d['start_date_stock'].split('/')[::-1]) #input(f"Enter start date (YYYY-MM-DD) for {stock_ticker}: ")
            end_date = "-".join(d['end_date_stock'].split('/')[::-1]) #input(f"Enter end date (YYYY-MM-DD) for {stock_ticker}: ")
            stock_data = get_stock_data_from_file(stock_ticker, start_date, end_date)
            beta = float(d['beta']) #float(input(f"Enter beta for {stock_ticker}: "))
            quantity = float(d['quantity']) #float(input(f"Enter quantity of {stock_ticker}: "))
            portfolio_stocks.append(stock_data)
            portfolio_tickers.append(stock_ticker)
            portfolio_betas.append(beta)
            portfolio_quantities.append(quantity)
            portfolio_stock_data[stock_ticker] = quantity  # Store stock name and quantity

        index_ticker = d['index_symbol'] #input("Enter the market index symbol: ")
        start_date = "-".join(d['start_date_index'].split('/')[::-1]) #input("Enter start date (YYYY-MM-DD) for the market index: ")
        end_date = "-".join(d['end_date_index'].split('/')[::-1]) #input("Enter end date (YYYY-MM-DD) for the market index: ")
        index_data = get_index_data_from_file(index_ticker, start_date, end_date)

        portfolio, portfolio_value, portfolio_weighted_beta = create_portfolio(portfolio_stocks, portfolio_tickers, portfolio_quantities, portfolio_betas)
        image, correlation, correlation_meaning = plot_price_relation(portfolio, index_data, "Portfolio", index_ticker)

        # Calculate total portfolio beta
        total_portfolio_beta = portfolio_weighted_beta * portfolio_value

        # Calculate portfolio value ratio with the index's current value
        index_current_value = index_data['Close'].iloc[-1]
        portfolio_index_value_ratio = portfolio_value / index_current_value

        # Calculate portfolio beta ratio with the index's value
        portfolio_index_beta_ratio = total_portfolio_beta / index_current_value

        # Additional feature: Calculate potential return from index hedge
        down_percentage = float(d['percentage_down']) #float(input("Enter the percentage your portfolio is expected to go down (e.g., 10 for 10%): "))
        return_from_hedge = portfolio_value * (down_percentage / 100)

        # Create JSON data
        data = {
            "image":f'data:image/png;base64, {image}',
            "Correlation": correlation,
            "Correlation Meaning": correlation_meaning,
            "Total Portfolio Value": portfolio_value,
            "Portfolio Weighted Beta": portfolio_weighted_beta,
            "Total Portfolio Beta": total_portfolio_beta,
            "Portfolio vs. Index Value Ratio": portfolio_index_value_ratio,
            "Portfolio vs. Index Beta Ratio": portfolio_index_beta_ratio,
            "Stock Data": portfolio_stock_data,  # Include stock name and quantity
            "Potential Return from Index Hedge": return_from_hedge
        }
        return {'success':True,'data':data}
    except:
        return {'msg':'something went wrong','success':False}


    
