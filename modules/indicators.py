# indicators.py

def add_indicators(hist):

    # SMA 50
    hist["SMA_50"] = (
        hist["Close"]
        .rolling(50)
        .mean()
    )

    # SMA 200
    hist["SMA_200"] = (
        hist["Close"]
        .rolling(200)
        .mean()
    )

    return hist

# RSI
    
    delta = hist["Close"].diff()
    
    gain = (
        delta.where(delta > 0, 0)
        .rolling(14)
        .mean()
    )
    
    loss = (
        -delta.where(delta < 0, 0)
        .rolling(14)
        .mean()
    )
    
    rs = gain / loss
    
    hist["RSI"] = 100 - (
        100 / (1 + rs)
    )