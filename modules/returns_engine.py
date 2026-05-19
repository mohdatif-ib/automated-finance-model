def calculate_returns(df):

    df["Returns"] = df["Adj Close"].pct_change()

    return df