import numpy as np

def calculate_beta(stock_returns, market_returns):

    covariance = np.cov(stock_returns, market_returns)[0][1]

    variance = np.var(market_returns)

    beta = covariance / variance

    return beta
