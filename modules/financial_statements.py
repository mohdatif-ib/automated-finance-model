import yfinance as yf

def fetch_financials(ticker):

    stock = yf.Ticker(ticker)

    return {
        "income_statement": stock.financials,
        "balance_sheet": stock.balance_sheet,
        "cashflow": stock.cashflow
    }