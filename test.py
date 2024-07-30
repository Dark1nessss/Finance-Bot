import yfinance as yf
import requests

# Your FMP API Key
FMP_API_KEY = 'I3nmChKQ7I4ecY8nONkcq7NAsDsE4AjM'

def fetch_from_yahoo_finance(symbol):
    ticker = yf.Ticker(symbol)
    info = ticker.info
    
    # Extracting data
    data = {
        'market_price': info.get('currentPrice', 'N/A'),
        'eps': info.get('earningsPerShare', 'N/A'),
        'forward_pe': info.get('forwardEps', 'N/A'),
        'growth_rate': 'N/A',  # Yahoo Finance does not directly provide this
        'net_income': info.get('netIncome', 'N/A'),
        'shareholders_equity': info.get('totalStockholderEquity', 'N/A'),
        'total_liabilities': info.get('totalLiabilitiesNetMinorityInterest', 'N/A'),
        'cash_flow': info.get('totalCashFromOperatingActivities', 'N/A'),
        'revenue': info.get('totalRevenue', 'N/A'),
        'profit_margin': info.get('profitMargins', 'N/A'),
        'dividend_yield': info.get('dividendYield', 'N/A'),
        'pe_ratio': info.get('trailingPE', 'N/A'),
        'beta': info.get('beta', 'N/A'),
        'market_cap': info.get('marketCap', 'N/A'),
        'enterprise_value': info.get('enterpriseValue', 'N/A'),
        'price_to_book': info.get('priceToBook', 'N/A'),
        'quick_ratio': info.get('quickRatio', 'N/A'),
        'current_ratio': info.get('currentRatio', 'N/A'),
        'return_on_assets': info.get('returnOnAssets', 'N/A'),
        'return_on_equity': info.get('returnOnEquity', 'N/A'),
        'debt_to_equity': info.get('debtToEquity', 'N/A'),
        'symbol': symbol
    }
    
    # Additional calculations if needed
    if data['forward_pe'] == 'N/A':
        eps = data.get('eps')
        market_price = data.get('market_price')
        if eps != 'N/A' and market_price != 'N/A':
            try:
                data['forward_pe'] = round(float(market_price) / float(eps), 2)
            except ZeroDivisionError:
                data['forward_pe'] = 'N/A'
    
    return data

def fetch_from_fmp(symbol):
    # API endpoints
    company_overview_url = f'https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={FMP_API_KEY}'
    income_statement_url = f'https://financialmodelingprep.com/api/v3/financials/income-statement/{symbol}?apikey={FMP_API_KEY}'
    balance_sheet_url = f'https://financialmodelingprep.com/api/v3/financials/balance-sheet-statement/{symbol}?apikey={FMP_API_KEY}'
    cash_flow_url = f'https://financialmodelingprep.com/api/v3/financials/cash-flow-statement/{symbol}?apikey={FMP_API_KEY}'
    ratios_url = f'https://financialmodelingprep.com/api/v3/ratios/{symbol}?apikey={FMP_API_KEY}'
    
    data = {}
    
    try:
        # Company Overview
        response = requests.get(company_overview_url)
        response.raise_for_status()
        overview = response.json()
        if overview:
            overview = overview[0]
            data.update({
                'market_price': overview.get('price', 'N/A'),
                'eps': overview.get('eps', 'N/A'),
                'forward_pe': 'N/A',  # Not provided in the overview
                'growth_rate': 'N/A',  # Not provided in the overview
                'net_income': overview.get('netIncome', 'N/A'),
                'shareholders_equity': overview.get('totalStockholderEquity', 'N/A'),
                'total_liabilities': overview.get('totalLiabilities', 'N/A'),
                'cash_flow': 'N/A',  # Not provided in the overview
                'revenue': overview.get('revenue', 'N/A'),
                'profit_margin': overview.get('profitMargin', 'N/A'),
                'dividend_yield': overview.get('dividendYield', 'N/A'),
                'pe_ratio': overview.get('peRatio', 'N/A'),
                'beta': overview.get('beta', 'N/A'),
                'market_cap': overview.get('marketCap', 'N/A'),
                'enterprise_value': overview.get('enterpriseValue', 'N/A'),
                'price_to_book': overview.get('priceToBook', 'N/A'),
                'quick_ratio': 'N/A',  # Not provided in the overview
                'current_ratio': 'N/A',  # Not provided in the overview
                'return_on_assets': 'N/A',  # Not provided in the overview
                'return_on_equity': 'N/A',  # Not provided in the overview
                'debt_to_equity': 'N/A',  # Not provided in the overview
                'symbol': symbol
            })
        
        # Income Statement
        response = requests.get(income_statement_url)
        response.raise_for_status()
        income_statement = response.json()
        if income_statement and 'financials' in income_statement:
            income = income_statement['financials'][0]
            data.update({
                'revenue': income.get('Revenue', 'N/A'),
                'net_income': income.get('Net Income', 'N/A'),
                'eps': income.get('Earnings Per Share', 'N/A')
            })
        
        # Balance Sheet
        response = requests.get(balance_sheet_url)
        response.raise_for_status()
        balance_sheet = response.json()
        if balance_sheet and 'balanceSheetStatements' in balance_sheet:
            bs = balance_sheet['balanceSheetStatements'][0]
            data.update({
                'shareholders_equity': bs.get('totalStockholderEquity', 'N/A'),
                'total_liabilities': bs.get('totalLiabilities', 'N/A')
            })
        
        # Cash Flow Statement
        response = requests.get(cash_flow_url)
        response.raise_for_status()
        cash_flow = response.json()
        if cash_flow and 'cashflowStatement' in cash_flow:
            cf = cash_flow['cashflowStatement'][0]
            data.update({
                'cash_flow': cf.get('totalCashFromOperatingActivities', 'N/A')
            })
        
        # Ratios
        response = requests.get(ratios_url)
        response.raise_for_status()
        ratios = response.json()
        if ratios and 'ratios' in ratios:
            ratio = ratios['ratios'][0]
            data.update({
                'profit_margin': ratio.get('netProfitMargin', 'N/A'),
                'dividend_yield': ratio.get('dividendYield', 'N/A'),
                'pe_ratio': ratio.get('peRatio', 'N/A'),
                'quick_ratio': ratio.get('quickRatio', 'N/A'),
                'current_ratio': ratio.get('currentRatio', 'N/A'),
                'return_on_assets': ratio.get('returnOnAssets', 'N/A'),
                'return_on_equity': ratio.get('returnOnEquity', 'N/A'),
                'debt_to_equity': ratio.get('debtToEquity', 'N/A')
            })
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from FMP: {e}")
    
    return data

def main():
    symbol = input("Enter the company symbol (e.g., NVDA, AAPL): ").upper()
    yahoo_data = fetch_from_yahoo_finance(symbol)
    fmp_data = fetch_from_fmp(symbol)
    
    print("\nYahoo Finance Data:")
    for key, value in yahoo_data.items():
        print(f"{key}: {value}")
    
    print("\nFMP Data:")
    if fmp_data:
        for key, value in fmp_data.items():
            print(f"{key}: {value}")
    else:
        print("No data found from FMP.")

if __name__ == "__main__":
    main()