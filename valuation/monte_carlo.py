from __future__ import annotations

import numpy as np
import pandas as pd

from valuation.dcf import calculate_dcf, calculate_dcf_vectorized


def run_monte_carlo_dcf(
    assumptions: dict,
    simulation_count: int = 10000,
    forecast_years: int = 5,
    random_seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(random_seed)
    n_sims = int(simulation_count)

    revenue_growth = rng.normal(
        assumptions["revenue_growth_mean"],
        assumptions["revenue_growth_std"],
        n_sims,
    )
    ebit_margin = rng.normal(
        assumptions["ebit_margin_mean"],
        assumptions["ebit_margin_std"],
        n_sims,
    )
    wacc = rng.normal(assumptions["wacc_mean"], assumptions["wacc_std"], n_sims)
    terminal_growth = rng.normal(
        assumptions["terminal_growth_mean"],
        assumptions["terminal_growth_std"],
        n_sims,
    )

    return calculate_dcf_vectorized(
        base_revenue=assumptions["base_revenue"],
        revenue_growth=revenue_growth,
        ebit_margin=ebit_margin,
        tax_rate=assumptions["tax_rate"],
        capex_pct_revenue=assumptions["capex_pct_revenue"],
        depreciation_pct_revenue=assumptions["depreciation_pct_revenue"],
        working_capital_pct_revenue=assumptions["working_capital_pct_revenue"],
        wacc=wacc,
        terminal_growth=terminal_growth,
        forecast_years=forecast_years,
        cash=assumptions["cash"],
        debt=assumptions["debt"],
        shares_outstanding=assumptions["shares_outstanding"],
    )


def valuation_statistics(results: pd.DataFrame) -> dict:
    values = results["intrinsic_value_per_share"].replace([np.inf, -np.inf], np.nan).dropna()
    if values.empty:
        empty = {
            "mean": np.nan,
            "median": np.nan,
            "mode": np.nan,
            "std_dev": np.nan,
            "min": np.nan,
            "max": np.nan,
            "p5": np.nan,
            "p10": np.nan,
            "p25": np.nan,
            "p50": np.nan,
            "p75": np.nan,
            "p90": np.nan,
            "p95": np.nan,
        }
        return empty

    percentiles = np.percentile(values, [5, 10, 25, 50, 75, 90, 95])

    hist_counts, hist_edges = np.histogram(values, bins=80)
    mode_idx = int(hist_counts.argmax())
    mode = float((hist_edges[mode_idx] + hist_edges[mode_idx + 1]) / 2.0)

    return {
        "mean": float(values.mean()),
        "median": float(values.median()),
        "mode": mode,
        "std_dev": float(values.std(ddof=0)),
        "min": float(values.min()),
        "max": float(values.max()),
        "p5": float(percentiles[0]),
        "p10": float(percentiles[1]),
        "p25": float(percentiles[2]),
        "p50": float(percentiles[3]),
        "p75": float(percentiles[4]),
        "p90": float(percentiles[5]),
        "p95": float(percentiles[6]),
    }


def probability_analysis(results: pd.DataFrame, current_price: float) -> dict:
    values = results["intrinsic_value_per_share"].replace([np.inf, -np.inf], np.nan).dropna()
    current_price = float(current_price or 0.0)
    if values.empty:
        return {
            "current_price": current_price,
            "fair_value_mean": np.nan,
            "probability_undervalued": np.nan,
            "probability_overvalued": np.nan,
            "margin_of_safety": np.nan,
        }

    fair_value_mean = float(values.mean())

    if current_price <= 0:
        probability_undervalued = np.nan
        probability_overvalued = np.nan
        margin_of_safety = np.nan
    else:
        probability_undervalued = float((values > current_price).mean())
        probability_overvalued = float(1.0 - probability_undervalued)
        margin_of_safety = float((fair_value_mean - current_price) / fair_value_mean) if fair_value_mean else np.nan

    return {
        "current_price": current_price,
        "fair_value_mean": fair_value_mean,
        "probability_undervalued": probability_undervalued,
        "probability_overvalued": probability_overvalued,
        "margin_of_safety": margin_of_safety,
    }


def scenario_analysis(stats: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"Scenario": "Bear Case", "Percentile": "10th", "Intrinsic Value": stats["p10"]},
            {"Scenario": "Base Case", "Percentile": "50th", "Intrinsic Value": stats["p50"]},
            {"Scenario": "Bull Case", "Percentile": "90th", "Intrinsic Value": stats["p90"]},
        ]
    )


def tornado_analysis(assumptions: dict, forecast_years: int) -> pd.DataFrame:
    base_value = calculate_dcf(
        base_revenue=assumptions["base_revenue"],
        revenue_growth=assumptions["revenue_growth_mean"],
        ebit_margin=assumptions["ebit_margin_mean"],
        tax_rate=assumptions["tax_rate"],
        capex_pct_revenue=assumptions["capex_pct_revenue"],
        depreciation_pct_revenue=assumptions["depreciation_pct_revenue"],
        working_capital_pct_revenue=assumptions["working_capital_pct_revenue"],
        wacc=assumptions["wacc_mean"],
        terminal_growth=assumptions["terminal_growth_mean"],
        forecast_years=forecast_years,
        cash=assumptions["cash"],
        debt=assumptions["debt"],
        shares_outstanding=assumptions["shares_outstanding"],
    )["intrinsic_value_per_share"]

    variables = [
        ("Revenue Growth", "revenue_growth_mean", "revenue_growth_std"),
        ("EBIT Margin", "ebit_margin_mean", "ebit_margin_std"),
        ("WACC", "wacc_mean", "wacc_std"),
        ("Terminal Growth", "terminal_growth_mean", "terminal_growth_std"),
    ]

    rows = []
    for label, mean_key, std_key in variables:
        low_assumptions = dict(assumptions)
        high_assumptions = dict(assumptions)
        low_assumptions[mean_key] = assumptions[mean_key] - assumptions[std_key]
        high_assumptions[mean_key] = assumptions[mean_key] + assumptions[std_key]

        low_value = calculate_dcf(
            base_revenue=low_assumptions["base_revenue"],
            revenue_growth=low_assumptions["revenue_growth_mean"],
            ebit_margin=low_assumptions["ebit_margin_mean"],
            tax_rate=low_assumptions["tax_rate"],
            capex_pct_revenue=low_assumptions["capex_pct_revenue"],
            depreciation_pct_revenue=low_assumptions["depreciation_pct_revenue"],
            working_capital_pct_revenue=low_assumptions["working_capital_pct_revenue"],
            wacc=low_assumptions["wacc_mean"],
            terminal_growth=low_assumptions["terminal_growth_mean"],
            forecast_years=forecast_years,
            cash=low_assumptions["cash"],
            debt=low_assumptions["debt"],
            shares_outstanding=low_assumptions["shares_outstanding"],
        )["intrinsic_value_per_share"]

        high_value = calculate_dcf(
            base_revenue=high_assumptions["base_revenue"],
            revenue_growth=high_assumptions["revenue_growth_mean"],
            ebit_margin=high_assumptions["ebit_margin_mean"],
            tax_rate=high_assumptions["tax_rate"],
            capex_pct_revenue=high_assumptions["capex_pct_revenue"],
            depreciation_pct_revenue=high_assumptions["depreciation_pct_revenue"],
            working_capital_pct_revenue=high_assumptions["working_capital_pct_revenue"],
            wacc=high_assumptions["wacc_mean"],
            terminal_growth=high_assumptions["terminal_growth_mean"],
            forecast_years=forecast_years,
            cash=high_assumptions["cash"],
            debt=high_assumptions["debt"],
            shares_outstanding=high_assumptions["shares_outstanding"],
        )["intrinsic_value_per_share"]

        rows.append(
            {
                "Variable": label,
                "Low Case": float(min(low_value, high_value)),
                "High Case": float(max(low_value, high_value)),
                "Base Value": float(base_value),
                "Impact": float(max(abs(low_value - base_value), abs(high_value - base_value))),
            }
        )

    return pd.DataFrame(rows).sort_values("Impact", ascending=True)
