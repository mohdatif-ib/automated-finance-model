# utils.py

import pandas as pd


def indian_number_format(num):

    if not isinstance(num, (int, float)):
        return num

    abs_num = abs(num)

    # Trillions
    if abs_num >= 1e12:
        return f"₹{num / 1e12:.2f} T"

    # Crores
    elif abs_num >= 1e7:
        return f"₹{num / 1e7:.2f} Cr"

    # Lakhs
    elif abs_num >= 1e5:
        return f"₹{num / 1e5:.2f} L"

    # Thousands
    elif abs_num >= 1e3:
        return f"₹{num / 1e3:.2f} K"

    else:
        return f"₹{num:.2f}"


def format_large_numbers(df):

    formatted_df = df.copy()

    for col in formatted_df.columns:

        formatted_df[col] = formatted_df[col].apply(
            indian_number_format
        )

    return formatted_df