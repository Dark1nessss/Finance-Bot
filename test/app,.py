from flask import Flask, render_template, jsonify
import requests
import pandas as pd
from config import API_KEY

app = Flask(__name__)

def fetch_top_stocks():
    """
    Fetch the top 10 active stocks from the FMP API.
    """
    url = f'https://financialmodelingprep.com/api/v3/stock_market/actives?apikey={API_KEY}'
    response = requests.get(url)
    data = response.json()
    return pd.DataFrame(data[:10])  # Fetch only top 10 stocks
def fetch_news(stock_symbol):
    """
    Fetch the latest news for a given stock symbol.
    """
    news_url = f'https://financialmodelingprep.com/api/v3/stock_news?tickers={stock_symbol}&limit=5&apikey={API_KEY}'  # Fetch only top 5 news articles per stock
    news_response = requests.get(news_url)
    news_data = news_response.json()
    # Ensure news_data is a list of dictionaries
    return news_data if isinstance(news_data, list) else []


def fetch_historical_data(stock_symbol):
    """
    Fetch historical price data for a given stock symbol.
    """
    historical_url = f'https://financialmodelingprep.com/api/v3/historical-price-full/{stock_symbol}?apikey={API_KEY}'
    response = requests.get(historical_url)
    data = response.json()
    return data['historical'][:30]  # Fetch only the last 30 days of data

def calculate_metrics(df):
    """
    Calculate additional financial metrics.
    """
    # Check if 'previousClose' column exists
    if 'previousClose' in df.columns:
        df['price_change'] = df['price'] - df['previousClose']
        df['price_change_pct'] = (df['price_change'] / df['previousClose']) * 100
    else:
        df['price_change'] = None
        df['price_change_pct'] = None
    return df

def get_stock_logo(symbol):
    """
    Get the stock logo URL using Clearbit Logo API.
    """
    logo_url = f'https://logo.clearbit.com/{symbol}.com'
    return logo_url

@app.route('/')
def index():
    # Fetch top 10 active stocks
    df = fetch_top_stocks()
    # Print DataFrame columns to inspect structure
    print(df.columns)
    # Calculate additional metrics
    df = calculate_metrics(df)
    # Fetch news for each stock
    news_data = {symbol: fetch_news(symbol) for symbol in df['symbol']}
    # Add logo URLs
    df['logo_url'] = df['symbol'].apply(get_stock_logo)
    # Convert DataFrame to dictionary for easy template rendering
    stocks_data = df.to_dict(orient='records')
    return render_template('index.html', stocks=stocks_data, news=news_data)

@app.route('/stock_details/<symbol>')
def stock_details(symbol):
    # Fetch detailed stock data
    stock_url = f'https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={API_KEY}'
    response = requests.get(stock_url)
    stock_data = response.json()

    # Fetch stock news
    news_data = fetch_news(symbol)

    # Fetch historical data for charts
    historical_data = fetch_historical_data(symbol)

    return render_template('stock_details.html', stock=stock_data[0], news=news_data, historical=historical_data)

if __name__ == '__main__':
    app.run(debug=True)
