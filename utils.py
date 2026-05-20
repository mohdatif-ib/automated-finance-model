# utils.py

import math
from numbers import Number


CURRENCY_SYMBOLS = {
    "INR": "₹",
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CNY": "¥",
    "CAD": "C$",
    "AUD": "A$",
    "CHF": "CHF ",
    "HKD": "HK$",
}


def get_currency_symbol(currency):
    if not currency:
        return ""

    return CURRENCY_SYMBOLS.get(currency.upper(), f"{currency.upper()} ")


def _is_number(num):
    return isinstance(num, Number) and not isinstance(num, bool)


def format_money(num, currency="INR", compact=True):
    if not _is_number(num) or not math.isfinite(num):
        return "N/A"

    symbol = get_currency_symbol(currency)

    if not compact:
        return f"{symbol}{num:,.2f}"

    abs_num = abs(num)
    units = [
        (1e12, "T"),
        (1e9, "B"),
        (1e6, "M"),
        (1e3, "K"),
    ]

    for value, suffix in units:
        if abs_num >= value:
            return f"{symbol}{num / value:.2f} {suffix}"

    return f"{symbol}{num:.2f}"


def indian_number_format(num):
    return format_money(num, "INR")


def format_large_numbers(df, currency="INR"):
    formatted_df = df.copy()

    for col in formatted_df.columns:
        formatted_df[col] = formatted_df[col].apply(
            lambda value: format_money(value, currency)
        )

    return formatted_df
