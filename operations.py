import yfinance as yf
import pandas as pd
from pymongo import MongoClient
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models import HoverTool, ColumnDataSource
from bokeh.resources import CDN
from flask_socketio import emit
import random
from bson import ObjectId

try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client.stock_data
    print("MongoDB connection established successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise

def fetch_and_store_data(ticker_symbol, period='6mo'):
    ticker = yf.Ticker(ticker_symbol)
    hist = ticker.history(period=period)
    hist.reset_index(inplace=True)
    hist_dict = hist.to_dict(orient="records")
    
    company_name = ticker.info.get('shortName', 'Unknown Firm')

    # Fetch financial metrics
    financials = {
        'market_price': ticker.info.get('currentPrice', 0),
        'eps': ticker.info.get('trailingEps', 0),
        'forward_pe': ticker.info.get('forwardPE', 0),
        'growth_rate': ticker.info.get('earningsGrowth', 0),
        'book_value_per_share': ticker.info.get('bookValue', 0),
        'net_income': ticker.financials.loc['Net Income', :].iloc[0] if 'Net Income' in ticker.financials.index else 0,
        'shareholders_equity': ticker.balance_sheet.loc['Total Stockholder Equity', :].iloc[0] if 'Total Stockholder Equity' in ticker.balance_sheet.index else 0,
        'total_liabilities': ticker.balance_sheet.loc['Total Liab', :].iloc[0] if 'Total Liab' in ticker.balance_sheet.index else 0,
        'current_assets': ticker.balance_sheet.loc['Total Current Assets', :].iloc[0] if 'Total Current Assets' in ticker.balance_sheet.index else 0,
        'current_liabilities': ticker.balance_sheet.loc['Total Current Liabilities', :].iloc[0] if 'Total Current Liabilities' in ticker.balance_sheet.index else 0,
        'cash_flow': ticker.cashflow.loc['Total Cash From Operating Activities', :].iloc[0] if 'Total Cash From Operating Activities' in ticker.cashflow.index else 0,
        'debt': ticker.balance_sheet.loc['Long Term Debt', :].iloc[0] if 'Long Term Debt' in ticker.balance_sheet.index else 0,
        'revenue': ticker.financials.loc['Total Revenue', :].iloc[0] if 'Total Revenue' in ticker.financials.index else 0,
        'gross_profit': ticker.financials.loc['Gross Profit', :].iloc[0] if 'Gross Profit' in ticker.financials.index else 0,
        'operating_margin': ticker.info.get('operatingMargins', 0),
        'profit_margin': ticker.info.get('profitMargins', 0),
        'revenue_growth': ticker.info.get('revenueGrowth', 0)
    }
    
    stocks_collection = db.stocks
    stocks_collection.update_one(
        {"symbol": ticker_symbol},
        {"$set": {"history": hist_dict, "name": company_name, "financials": financials}},
        upsert=True
    )

def calculate_ratios_and_intrinsic_value(financials):
    market_price = financials['market_price']
    eps = financials['eps']
    forward_pe = financials['forward_pe']
    growth_rate = financials['growth_rate']
    book_value_per_share = financials['book_value_per_share']
    net_income = financials['net_income']
    shareholders_equity = financials['shareholders_equity']
    total_liabilities = financials['total_liabilities']
    current_assets = financials['current_assets']
    current_liabilities = financials['current_liabilities']
    cash_flow = financials['cash_flow']
    debt = financials['debt']
    revenue = financials['revenue']
    gross_profit = financials['gross_profit']
    operating_margin = financials['operating_margin']
    profit_margin = financials['profit_margin']
    revenue_growth = financials['revenue_growth']
    
    price_to_earnings_ratio = market_price / eps if eps else float('inf')  # P/E
    price_to_book_ratio = market_price / book_value_per_share if book_value_per_share else float('inf')  # P/B
    debt_to_equity_ratio = total_liabilities / shareholders_equity if shareholders_equity else float('inf')  # D/E
    return_on_equity = net_income / shareholders_equity if shareholders_equity else 0  # ROE
    current_ratio = current_assets / current_liabilities if current_liabilities else 0
    price_to_earnings_to_growth_ratio = forward_pe / (growth_rate * 100) if growth_rate else float('inf')  # PEG
    debt_to_equity = debt / shareholders_equity if shareholders_equity else float('inf')  # D/E
    profit_margin_to_revenue = profit_margin * 100 if profit_margin else 0
    
    # Intrinsic value calculation with increased margin of error
    intrinsic_value = (eps * (1 + 0.05) / 0.10) if eps else 0  # Assuming 5% growth and 10% discount rate
    margin_of_error = intrinsic_value * 0.30  # 30% margin of error
    intrinsic_value_lower = intrinsic_value - margin_of_error
    intrinsic_value_upper = intrinsic_value + margin_of_error
    
    return (price_to_earnings_ratio, price_to_book_ratio, debt_to_equity_ratio, return_on_equity, current_ratio, 
            intrinsic_value, price_to_earnings_to_growth_ratio, debt_to_equity, profit_margin_to_revenue, 
            intrinsic_value_lower, intrinsic_value_upper, revenue_growth)

def get_recommendation(data, financials):
    df = pd.DataFrame(data)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    
    ma20_latest = df['MA20'].iloc[-1]
    ma50_latest = df['MA50'].iloc[-1]
    
    (pe_ratio, pb_ratio, de_ratio, roe, current_ratio, intrinsic_value, peg_ratio, debt_to_equity, 
     profit_margin_to_revenue, intrinsic_value_lower, intrinsic_value_upper, revenue_growth) = calculate_ratios_and_intrinsic_value(financials)
    
    market_price = financials['market_price']
    
    pe_threshold = 25  # Industry-dependent
    pb_threshold = 3   # Industry-dependent
    de_threshold = 1.5
    current_ratio_threshold = 1.5
    peg_threshold = 1.0  # PEG ratio below 1 is generally considered good
    profit_margin_threshold = 10  # Example threshold for profit margin to revenue
    revenue_growth_threshold = 0.1  # 10% revenue growth considered positive

    recommendation = "Hold"
    explanation = "Based on current analysis, holding the stock is recommended."

    if ma20_latest > ma50_latest and market_price < intrinsic_value_upper:
        if (pe_ratio < pe_threshold and pb_ratio < pb_threshold and de_ratio < de_threshold and 
            current_ratio > current_ratio_threshold and revenue_growth > revenue_growth_threshold):
            recommendation = "Buy"
            explanation = (
                f"**Buy Recommendation:**\n"
                f"The 20-day moving average (MA20: {ma20_latest:.2f}) is above the 50-day moving average (MA50: {ma50_latest:.2f}), indicating an upward trend in the stock price.\n"
                f"The stock is undervalued, with an intrinsic value range (${intrinsic_value_lower:.2f} - ${intrinsic_value_upper:.2f}) higher than the current market price (${market_price:.2f}).\n"
                f"Financial ratios support this recommendation:\n"
                f"- Price to Earnings Ratio (P/E): {pe_ratio:.2f} (below the threshold of {pe_threshold})\n"
                f"- Price to Book Ratio (P/B): {pb_ratio:.2f} (below the threshold of {pb_threshold})\n"
                f"- Debt to Equity Ratio (D/E): {de_ratio:.2f} (below the threshold of {de_threshold})\n"
                f"- Current Ratio: {current_ratio:.2f} (above the threshold of {current_ratio_threshold})\n"
                f"- Price to Earnings to Growth Ratio (PEG): {peg_ratio:.2f} (below the threshold of {peg_threshold})\n"
                f"- Debt to Equity: {debt_to_equity:.2f} (below the threshold of {de_threshold})\n"
                f"- Profit Margin to Revenue: {profit_margin_to_revenue:.2f}% (above the threshold of {profit_margin_threshold}%)\n"
                f"- Revenue Growth: {revenue_growth:.2f}% (above the threshold of {revenue_growth_threshold}%)\n"
                f"These indicators suggest that the stock is reasonably priced and financially stable, making it a good buy opportunity."
            )
    elif ma20_latest < ma50_latest or market_price > intrinsic_value_lower:
        if (pe_ratio > pe_threshold or pb_ratio > pb_threshold or de_ratio > de_threshold or 
            current_ratio < current_ratio_threshold or revenue_growth < revenue_growth_threshold):
            recommendation = "Sell"
            explanation = (
                f"**Sell Recommendation:**\n"
                f"The 20-day moving average (MA20: {ma20_latest:.2f}) is below the 50-day moving average (MA50: {ma50_latest:.2f}), indicating a downward trend in the stock price.\n"
                f"The stock is overvalued, with an intrinsic value range (${intrinsic_value_lower:.2f} - ${intrinsic_value_upper:.2f}) lower than the current market price (${market_price:.2f}).\n"
                f"Financial ratios support this recommendation:\n"
                f"- Price to Earnings Ratio (P/E): {pe_ratio:.2f} (above the threshold of {pe_threshold})\n"
                f"- Price to Book Ratio (P/B): {pb_ratio:.2f} (above the threshold of {pb_threshold})\n"
                f"- Debt to Equity Ratio (D/E): {de_ratio:.2f} (above the threshold of {de_threshold})\n"
                f"- Current Ratio: {current_ratio:.2f} (below the threshold of {current_ratio_threshold})\n"
                f"- Price to Earnings to Growth Ratio (PEG): {peg_ratio:.2f} (above the threshold of {peg_threshold})\n"
                f"- Debt to Equity: {debt_to_equity:.2f} (above the threshold of {de_threshold})\n"
                f"- Profit Margin to Revenue: {profit_margin_to_revenue:.2f}% (below the threshold of {profit_margin_threshold}%)\n"
                f"- Revenue Growth: {revenue_growth:.2f}% (below the threshold of {revenue_growth_threshold}%)\n"
                f"These indicators suggest that the stock is overpriced and may face financial instability, making it a good sell opportunity."
            )
    else:
        explanation = (
            f"**Hold Recommendation:**\n"
            f"The 20-day moving average (MA20: {ma20_latest:.2f}) is close to the 50-day moving average (MA50: {ma50_latest:.2f}), indicating no significant trend.\n"
            f"The stock's market price (${market_price:.2f}) is within the intrinsic value range (${intrinsic_value_lower:.2f} - ${intrinsic_value_upper:.2f}).\n"
            f"Financial ratios support a hold decision:\n"
            f"- Price to Earnings Ratio (P/E): {pe_ratio:.2f} (below the threshold of {pe_threshold})\n"
            f"- Price to Book Ratio (P/B): {pb_ratio:.2f} (below the threshold of {pb_threshold})\n"
            f"- Debt to Equity Ratio (D/E): {de_ratio:.2f} (below the threshold of {de_threshold})\n"
            f"- Current Ratio: {current_ratio:.2f} (above the threshold of {current_ratio_threshold})\n"
            f"- Price to Earnings to Growth Ratio (PEG): {peg_ratio:.2f} (below the threshold of {peg_threshold})\n"
            f"- Debt to Equity: {debt_to_equity:.2f} (below the threshold of {de_threshold})\n"
            f"- Profit Margin to Revenue: {profit_margin_to_revenue:.2f}% (above the threshold of {profit_margin_threshold}%)\n"
            f"- Revenue Growth: {revenue_growth:.2f}% (above the threshold of {revenue_growth_threshold}%)\n"
            f"These indicators suggest that the stock is fairly priced and financially stable, making it a hold opportunity."
        )
    
    return recommendation, explanation

def create_detailed_plot(data):
    df = pd.DataFrame(data)
    df['Date'] = pd.to_datetime(df['Date'])
    
    p = figure(x_axis_type="datetime", title="Stock Price Movement", width=800, height=400)
    source = ColumnDataSource(df)
    
    p.line('Date', 'Close', color='navy', legend_label='Close Price', source=source)
    p.line('Date', 'MA20', color='orange', legend_label='20-Day MA', source=source)
    p.line('Date', 'MA50', color='green', legend_label='50-Day MA', source=source)
    
    tooltips = [("Date", "@Date{%F}"), ("Close", "@Close{0.2f}")]
    
    hover_tool = HoverTool(tooltips=tooltips, formatters={'@Date': 'datetime'})
    p.add_tools(hover_tool)
    
    p.legend.location = "top_left"
    p.xaxis.axis_label = "Date"
    p.yaxis.axis_label = "Price (USD)"
    
    script, div = components(p)
    cdn_js = CDN.js_files[0] if CDN.js_files else None
    cdn_css = CDN.css_files[0] if CDN.css_files else None
    
    return script, div, cdn_js, cdn_css

def validate_user(username, password):
    user = db.users.find_one({"username": username, "password": password})
    return user

def add_alert(username, ticker_symbol, condition, price):
    alerts_collection = db.alerts
    alert = {
        "username": username,
        "ticker_symbol": ticker_symbol,
        "condition": condition,
        "price": price
    }
    alerts_collection.update_one(
        {"username": username, "ticker_symbol": ticker_symbol},
        {"$set": alert},
        upsert=True
    )

def get_user_alerts(username):
    try:
        alerts_collection = db.alerts
        alerts = list(alerts_collection.find({"username": username}))
        
        for alert in alerts:
            if '_id' in alert:
                alert['_id'] = str(alert['_id'])
        
        print(f"Fetched alerts for {username}: {alerts}")
        return alerts
    except Exception as e:
        print(f"Error in get_user_alerts: {e}")
        raise

def remove_alert(username, ticker_symbol):
    alerts_collection = db.alerts
    alerts_collection.delete_one({"username": username, "ticker_symbol": ticker_symbol})

def check_alerts_simulated(socketio, ticker_symbol, simulated_price):
    alerts_collection = db.alerts
    alerts = list(alerts_collection.find({"ticker_symbol": ticker_symbol}))

    for alert in alerts:
        condition = alert['condition']
        price = alert['price']
        if (condition == "above" and simulated_price > price) or (condition == "below" and simulated_price < price):
            socketio.emit('price_alert', {
                'ticker': ticker_symbol,
                'condition': condition,
                'price': price,
                'current_price': simulated_price
            })

def simulate_data_changes(socketio, ticker_symbol):
    simulated_price = random.uniform(75, 76)
    check_alerts_simulated(socketio, ticker_symbol, simulated_price)
    return simulated_price