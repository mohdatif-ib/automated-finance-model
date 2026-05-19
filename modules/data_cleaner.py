import pandas as pd


def align_data(stock_df, benchmark_df):
    merged = pd.merge(
        stock_df,
        benchmark_df,
        left_index=True,
        right_index=True,
        suffixes=("_stock", "_market")
    )

    merged = merged.dropna()

    return merged