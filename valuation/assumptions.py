from __future__ import annotations

from dataclasses import asdict, dataclass
from numbers import Number

import numpy as np
import pandas as pd


def _is_number(value) -> bool:
    return isinstance(value, Number) and not isinstance(value, bool) and np.isfinite(value)


def _to_float(value, default=None):
    try:
        numeric = pd.to_numeric(value)
    except Exception:
        return default

    if _is_number(numeric):
        return float(numeric)

    return default


def _get_first(source, keys, default=None):
    if not source:
        return default

    for key in keys:
        try:
            value = source.get(key)
        except Exception:
            continue

        if value is None:
            continue

        try:
            if pd.isna(value):
                continue
        except Exception:
            pass

        return value

    return default


def statement_row(statement: pd.DataFrame, row_names) -> pd.Series:
    if statement is None or statement.empty:
        return pd.Series(dtype="float64")

    for row_name in row_names:
        if row_name in statement.index:
            values = pd.to_numeric(statement.loc[row_name], errors="coerce").dropna()
            if not values.empty:
                try:
                    values.index = pd.to_datetime(values.index)
                    values = values.sort_index()
                except Exception:
                    values = values.iloc[::-1]
                return values.astype(float)

    return pd.Series(dtype="float64")


def latest_statement_value(statement: pd.DataFrame, row_names, default=0.0) -> float:
    series = statement_row(statement, row_names)
    if series.empty:
        return float(default)
    return float(series.iloc[-1])


def average_ratio(numerator: pd.Series, denominator: pd.Series, default: float) -> float:
    if numerator.empty or denominator.empty:
        return float(default)

    aligned = pd.concat([numerator, denominator], axis=1).dropna()
    if aligned.empty:
        return float(default)

    denom = aligned.iloc[:, 1].replace(0, np.nan)
    ratio = aligned.iloc[:, 0] / denom
    ratio = ratio.replace([np.inf, -np.inf], np.nan).dropna()

    if ratio.empty:
        return float(default)

    return float(ratio.mean())


def historical_growth_stats(revenue: pd.Series, info: dict) -> tuple[float, float]:
    if revenue is not None and len(revenue.dropna()) >= 2:
        growth = revenue.pct_change().replace([np.inf, -np.inf], np.nan).dropna()
        growth = growth[(growth > -0.8) & (growth < 2.0)]
        if not growth.empty:
            mean = float(np.clip(growth.mean(), -0.05, 0.30))
            std = float(np.clip(growth.std(ddof=0), 0.01, 0.20))
            return mean, max(std, 0.03)

    revenue_growth = _to_float(_get_first(info, ["revenueGrowth"]), None)
    if revenue_growth is None:
        revenue_growth = 0.08

    return float(np.clip(revenue_growth, -0.05, 0.25)), 0.05


@dataclass(frozen=True)
class DCFAssumptions:
    ticker: str
    company_name: str
    currency: str
    current_price: float
    shares_outstanding: float
    base_revenue: float
    revenue_growth_mean: float
    revenue_growth_std: float
    ebit_margin_mean: float
    ebit_margin_std: float
    tax_rate: float
    capex_pct_revenue: float
    depreciation_pct_revenue: float
    working_capital_pct_revenue: float
    wacc_mean: float
    wacc_std: float
    terminal_growth_mean: float
    terminal_growth_std: float
    cash: float
    debt: float
    market_cap: float
    beta: float

    def to_dict(self) -> dict:
        return asdict(self)


def build_baseline_assumptions(
    ticker: str,
    info: dict,
    fast_info: dict,
    financials: pd.DataFrame,
    balance_sheet: pd.DataFrame,
    cashflow: pd.DataFrame,
    current_price: float | None = None,
) -> DCFAssumptions:
    info = info or {}
    fast_info = fast_info or {}

    currency = (
        _get_first(info, ["currency"])
        or _get_first(fast_info, ["currency"])
        or ("INR" if ticker.endswith((".NS", ".BO")) else "USD")
    )
    company_name = _get_first(info, ["longName", "shortName"], ticker)

    revenue = statement_row(financials, ["Total Revenue", "Operating Revenue"])
    base_revenue = float(revenue.iloc[-1]) if not revenue.empty else 0.0

    current_price = _to_float(
        current_price,
        _to_float(_get_first(fast_info, ["lastPrice", "last_price"]), 0.0),
    )
    shares = _to_float(_get_first(info, ["sharesOutstanding"]), None)
    if shares is None:
        shares = _to_float(_get_first(fast_info, ["shares"]), None)

    market_cap = _to_float(_get_first(info, ["marketCap"]), None)
    if market_cap is None:
        market_cap = _to_float(_get_first(fast_info, ["marketCap", "market_cap"]), None)

    if shares is None and market_cap and current_price:
        shares = market_cap / current_price
    if market_cap is None and shares and current_price:
        market_cap = shares * current_price

    shares = float(shares or 1.0)
    market_cap = float(market_cap or shares * (current_price or 0.0))

    revenue_growth_mean, revenue_growth_std = historical_growth_stats(revenue, info)

    ebit = statement_row(financials, ["EBIT", "Operating Income", "Operating Income Loss"])
    ebit_margin = average_ratio(ebit, revenue, 0.12)
    if len(ebit.dropna()) >= 2 and len(revenue.dropna()) >= 2:
        margin_series = pd.concat([ebit, revenue], axis=1).dropna()
        margin_std = (margin_series.iloc[:, 0] / margin_series.iloc[:, 1]).std(ddof=0)
        ebit_margin_std = float(np.clip(margin_std if np.isfinite(margin_std) else 0.03, 0.01, 0.12))
    else:
        ebit_margin_std = 0.03
    ebit_margin = float(np.clip(ebit_margin, -0.10, 0.45))

    tax_provision = statement_row(financials, ["Tax Provision", "Income Tax Expense"])
    pretax_income = statement_row(financials, ["Pretax Income", "Income Before Tax"])
    tax_rate = average_ratio(tax_provision, pretax_income, 0.25)
    tax_rate = float(np.clip(abs(tax_rate), 0.05, 0.40))

    capex = statement_row(cashflow, ["Capital Expenditure", "Capital Expenditures"])
    capex_pct = abs(average_ratio(capex, revenue, 0.05))
    capex_pct = float(np.clip(capex_pct, 0.00, 0.35))

    depreciation = statement_row(
        cashflow,
        [
            "Depreciation And Amortization",
            "Depreciation Amortization Depletion",
            "Depreciation",
        ],
    )
    depreciation_pct = abs(average_ratio(depreciation, revenue, 0.03))
    depreciation_pct = float(np.clip(depreciation_pct, 0.00, 0.25))

    current_assets = statement_row(balance_sheet, ["Current Assets", "Total Current Assets"])
    current_liabilities = statement_row(balance_sheet, ["Current Liabilities", "Total Current Liabilities"])
    if not current_assets.empty and not current_liabilities.empty and not revenue.empty:
        working_capital = current_assets.subtract(current_liabilities, fill_value=np.nan)
        working_capital_pct = average_ratio(working_capital, revenue, 0.10)
    else:
        working_capital_pct = 0.10
    working_capital_pct = float(np.clip(working_capital_pct, -0.20, 0.40))

    cash = latest_statement_value(
        balance_sheet,
        ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"],
        0.0,
    )
    debt = latest_statement_value(balance_sheet, ["Total Debt", "Long Term Debt"], 0.0)

    beta = _to_float(_get_first(info, ["beta"]), 1.0)
    beta = float(np.clip(beta or 1.0, 0.4, 2.5))

    interest_expense = abs(latest_statement_value(financials, ["Interest Expense"], 0.0))
    pre_tax_cost_debt = interest_expense / debt if debt > 0 and interest_expense > 0 else None

    is_indian_listing = ticker.endswith((".NS", ".BO")) or currency == "INR"
    risk_free_rate = 0.07 if is_indian_listing else 0.045
    equity_risk_premium = 0.055
    cost_equity = risk_free_rate + beta * equity_risk_premium
    cost_debt = float(np.clip(pre_tax_cost_debt, 0.04, 0.16)) if pre_tax_cost_debt else risk_free_rate + 0.025

    invested_capital = market_cap + max(debt, 0.0)
    equity_weight = market_cap / invested_capital if invested_capital > 0 else 0.85
    debt_weight = 1.0 - equity_weight
    wacc = equity_weight * cost_equity + debt_weight * cost_debt * (1.0 - tax_rate)
    wacc = float(np.clip(wacc, 0.06, 0.20))

    terminal_growth = 0.045 if is_indian_listing else 0.025
    terminal_growth = min(terminal_growth, wacc - 0.02)

    return DCFAssumptions(
        ticker=ticker,
        company_name=str(company_name),
        currency=str(currency),
        current_price=float(current_price or 0.0),
        shares_outstanding=shares,
        base_revenue=base_revenue,
        revenue_growth_mean=revenue_growth_mean,
        revenue_growth_std=revenue_growth_std,
        ebit_margin_mean=ebit_margin,
        ebit_margin_std=ebit_margin_std,
        tax_rate=tax_rate,
        capex_pct_revenue=capex_pct,
        depreciation_pct_revenue=depreciation_pct,
        working_capital_pct_revenue=working_capital_pct,
        wacc_mean=wacc,
        wacc_std=0.015,
        terminal_growth_mean=float(np.clip(terminal_growth, 0.00, 0.06)),
        terminal_growth_std=0.005,
        cash=float(max(cash, 0.0)),
        debt=float(max(debt, 0.0)),
        market_cap=float(max(market_cap, 0.0)),
        beta=beta,
    )

