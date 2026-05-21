from __future__ import annotations

import numpy as np
import pandas as pd


def _as_1d_array(value):
    return np.asarray(value, dtype=float).reshape(-1)


def calculate_dcf_vectorized(
    base_revenue: float,
    revenue_growth,
    ebit_margin,
    tax_rate: float,
    capex_pct_revenue: float,
    depreciation_pct_revenue: float,
    working_capital_pct_revenue: float,
    wacc,
    terminal_growth,
    forecast_years: int,
    cash: float,
    debt: float,
    shares_outstanding: float,
) -> pd.DataFrame:
    revenue_growth = _as_1d_array(revenue_growth)
    ebit_margin = _as_1d_array(ebit_margin)
    wacc = _as_1d_array(wacc)
    terminal_growth = _as_1d_array(terminal_growth)

    n_sims = max(len(revenue_growth), len(ebit_margin), len(wacc), len(terminal_growth))
    revenue_growth = np.resize(revenue_growth, n_sims)
    ebit_margin = np.resize(ebit_margin, n_sims)
    wacc = np.resize(wacc, n_sims)
    terminal_growth = np.resize(terminal_growth, n_sims)

    revenue_growth = np.clip(revenue_growth, -0.30, 0.60)
    ebit_margin = np.clip(ebit_margin, -0.20, 0.65)
    wacc = np.clip(wacc, 0.025, 0.35)
    terminal_growth = np.minimum(np.clip(terminal_growth, -0.03, 0.08), wacc - 0.005)

    years = np.arange(1, int(forecast_years) + 1, dtype=float)
    revenue = float(base_revenue) * np.power(1.0 + revenue_growth[:, None], years)

    prior_revenue = np.concatenate(
        [np.full((n_sims, 1), float(base_revenue)), revenue[:, :-1]],
        axis=1,
    )
    revenue_change = revenue - prior_revenue

    ebit = revenue * ebit_margin[:, None]
    nopat = ebit * (1.0 - float(tax_rate))
    depreciation = revenue * float(depreciation_pct_revenue)
    capex = revenue * float(capex_pct_revenue)
    change_working_capital = revenue_change * float(working_capital_pct_revenue)

    free_cash_flow = nopat + depreciation - capex - change_working_capital
    discount_factors = np.power(1.0 + wacc[:, None], years)
    pv_free_cash_flow = free_cash_flow / discount_factors

    terminal_value = (
        free_cash_flow[:, -1]
        * (1.0 + terminal_growth)
        / np.maximum(wacc - terminal_growth, 0.005)
    )
    pv_terminal_value = terminal_value / np.power(1.0 + wacc, float(forecast_years))

    enterprise_value = pv_free_cash_flow.sum(axis=1) + pv_terminal_value
    equity_value = enterprise_value + float(cash) - float(debt)
    intrinsic_value = equity_value / max(float(shares_outstanding), 1.0)

    return pd.DataFrame(
        {
            "revenue_growth": revenue_growth,
            "ebit_margin": ebit_margin,
            "wacc": wacc,
            "terminal_growth": terminal_growth,
            "enterprise_value": enterprise_value,
            "equity_value": equity_value,
            "intrinsic_value_per_share": intrinsic_value,
        }
    )


def calculate_dcf(
    base_revenue: float,
    revenue_growth: float,
    ebit_margin: float,
    tax_rate: float,
    capex_pct_revenue: float,
    depreciation_pct_revenue: float,
    working_capital_pct_revenue: float,
    wacc: float,
    terminal_growth: float,
    forecast_years: int,
    cash: float,
    debt: float,
    shares_outstanding: float,
) -> dict:
    result = calculate_dcf_vectorized(
        base_revenue=base_revenue,
        revenue_growth=np.array([revenue_growth]),
        ebit_margin=np.array([ebit_margin]),
        tax_rate=tax_rate,
        capex_pct_revenue=capex_pct_revenue,
        depreciation_pct_revenue=depreciation_pct_revenue,
        working_capital_pct_revenue=working_capital_pct_revenue,
        wacc=np.array([wacc]),
        terminal_growth=np.array([terminal_growth]),
        forecast_years=forecast_years,
        cash=cash,
        debt=debt,
        shares_outstanding=shares_outstanding,
    )
    return result.iloc[0].to_dict()


def forecast_dcf_schedule(
    base_revenue: float,
    revenue_growth: float,
    ebit_margin: float,
    tax_rate: float,
    capex_pct_revenue: float,
    depreciation_pct_revenue: float,
    working_capital_pct_revenue: float,
    wacc: float,
    terminal_growth: float,
    forecast_years: int,
) -> pd.DataFrame:
    years = np.arange(1, int(forecast_years) + 1, dtype=float)
    revenue = float(base_revenue) * np.power(1.0 + float(revenue_growth), years)
    prior_revenue = np.concatenate([[float(base_revenue)], revenue[:-1]])
    revenue_change = revenue - prior_revenue

    ebit = revenue * float(ebit_margin)
    nopat = ebit * (1.0 - float(tax_rate))
    depreciation = revenue * float(depreciation_pct_revenue)
    capex = revenue * float(capex_pct_revenue)
    change_working_capital = revenue_change * float(working_capital_pct_revenue)
    free_cash_flow = nopat + depreciation - capex - change_working_capital
    pv_fcf = free_cash_flow / np.power(1.0 + float(wacc), years)

    terminal_growth = min(float(terminal_growth), float(wacc) - 0.005)
    terminal_value = free_cash_flow[-1] * (1.0 + terminal_growth) / max(float(wacc) - terminal_growth, 0.005)
    pv_terminal_value = terminal_value / np.power(1.0 + float(wacc), float(forecast_years))

    schedule = pd.DataFrame(
        {
            "Year": [f"Year {int(year)}" for year in years],
            "Revenue": revenue,
            "EBIT": ebit,
            "NOPAT": nopat,
            "Depreciation": depreciation,
            "CapEx": capex,
            "Change in Working Capital": change_working_capital,
            "Free Cash Flow": free_cash_flow,
            "Present Value of FCF": pv_fcf,
        }
    )
    schedule.loc[len(schedule)] = [
        "Terminal Value",
        np.nan,
        np.nan,
        np.nan,
        np.nan,
        np.nan,
        np.nan,
        terminal_value,
        pv_terminal_value,
    ]
    return schedule

