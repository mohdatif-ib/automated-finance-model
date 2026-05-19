import matplotlib.pyplot as plt

def plot_stock_price(df):

    plt.figure(figsize=(12,6))

    plt.plot(df.index, df["Adj Close"])

    plt.title("Stock Price")

    plt.xlabel("Date")

    plt.ylabel("Price")

    plt.show()