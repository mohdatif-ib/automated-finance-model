import requests
import pandas as pd
from config import API_KEY

def fetch_weekly_data(symbol):

    url = (
        "https://www.alphavantage.co/query"
        "?function=TIME_SERIES_WEEKLY_ADJUSTED"
        f"&symbol={symbol}"
        "&outputsize=full"
        f"&apikey={API_KEY}"
    )

    response = requests.get(url)
    data = response.json()
    
    response = requests.get(url)

    data = response.json()
    print(data)

# Check API response
    if "Weekly Adjusted Time Series" not in data:
        print(data)
    raise Exception("API response invalid")

    weekly = data["Weekly Adjusted Time Series"]

    df = pd.DataFrame.from_dict(weekly, orient="index")
    


    df = pd.DataFrame.from_dict(weekly, orient="index")

    df = df.rename(columns={
        "1. open": "Open",
        "2. high": "High",
        "3. low": "Low",
        "4. close": "Close",
        "5. adjusted close": "Adj Close",
        "6. volume": "Volume"
    })

    df.index = pd.to_datetime(df.index)

    df = df.astype(float)

    df = df.sort_index()

    return df