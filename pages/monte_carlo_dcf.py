from __future__ import annotations

from io import StringIO
import time

import pandas as pd
import plotly.express as px
import streamlit as st
import yfinance as yf

from charts.monte_carlo_charts import (
    create_cumulative_distribution_chart,
    create_intrinsic_value_histogram,
    create_probability_density_chart,
    create_tornado_chart,
)
from utils import format_money
from modules.nifty50 import NIFTY_50_COMPANIES
from valuation.assumptions import build_baseline_assumptions
from valuation.dcf import calculate_dcf, forecast_dcf_schedule
from valuation.monte_carlo import (
    probability_analysis,
    run_monte_carlo_dcf,
    scenario_analysis,
    tornado_analysis,
    valuation_statistics,
)


@st.cache_resource(ttl=3600)
def get_yahoo_ticker(ticker: str):
    return yf.Ticker(ticker)


@st.cache_data(ttl=3600, show_spinner=False)
def load_company_financial_data(ticker: str) -> dict:
    stock = get_yahoo_ticker(ticker)

    try:
        info = dict(stock.info or {})
    except Exception:
        info = {}

    try:
        fast_info = dict(stock.fast_info or {})
    except Exception:
        fast_info = {}

    try:
        hist = stock.history(period="1y", interval="1d", auto_adjust=False)
    except Exception:
        hist = pd.DataFrame()

    current_price = 0.0
    if not hist.empty and "Close" in hist.columns:
        current_price = float(hist["Close"].dropna().iloc[-1])
    else:
        current_price = float(fast_info.get("lastPrice") or fast_info.get("last_price") or 0.0)

    return {
        "info": info,
        "fast_info": fast_info,
        "financials": stock.financials,
        "balance_sheet": stock.balance_sheet,
        "cashflow": stock.cashflow,
        "quarterly_financials": stock.quarterly_financials,
        "quarterly_balance_sheet": stock.quarterly_balance_sheet,
        "quarterly_cashflow": stock.quarterly_cashflow,
        "history": hist,
        "current_price": current_price,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def calculate_company_monte_carlo_summary(
    company_name: str,
    ticker: str,
    simulation_count: int,
    forecast_years: int,
    random_seed: int,
) -> dict:
    try:
        data = load_company_financial_data(ticker)
        baseline = build_baseline_assumptions(
            ticker=ticker,
            info=data["info"],
            fast_info=data["fast_info"],
            financials=data["financials"],
            balance_sheet=data["balance_sheet"],
            cashflow=data["cashflow"],
            current_price=data["current_price"],
        )

        if baseline.base_revenue <= 0:
            return {
                "Company": company_name,
                "Ticker": ticker,
                "Status": "No revenue data",
            }

        assumptions = baseline.to_dict()
        assumptions["terminal_growth_mean"] = min(
            assumptions["terminal_growth_mean"],
            assumptions["wacc_mean"] - 0.005,
        )

        results = run_monte_carlo_dcf(
            assumptions=assumptions,
            simulation_count=simulation_count,
            forecast_years=forecast_years,
            random_seed=random_seed,
        )
        stats = valuation_statistics(results)
        probability = probability_analysis(results, assumptions["current_price"])

        current_price = probability["current_price"]
        fair_value_mean = probability["fair_value_mean"]
        upside_to_mean = (
            (fair_value_mean - current_price) / current_price
            if current_price and pd.notna(fair_value_mean)
            else pd.NA
        )

        return {
            "Company": company_name,
            "Ticker": ticker,
            "Yahoo Name": baseline.company_name,
            "Currency": baseline.currency,
            "Current Price": current_price,
            "Fair Value Mean": fair_value_mean,
            "Median Value": stats["median"],
            "Bear Case P10": stats["p10"],
            "Bull Case P90": stats["p90"],
            "Probability Undervalued": probability["probability_undervalued"],
            "Margin of Safety": probability["margin_of_safety"],
            "Upside to Mean": upside_to_mean,
            "Revenue Growth Mean": assumptions["revenue_growth_mean"],
            "EBIT Margin Mean": assumptions["ebit_margin_mean"],
            "WACC Mean": assumptions["wacc_mean"],
            "Terminal Growth Mean": assumptions["terminal_growth_mean"],
            "Status": "OK",
        }
    except Exception as exc:
        return {
            "Company": company_name,
            "Ticker": ticker,
            "Status": f"Error: {exc}",
        }


def render_nifty_50_batch_monte_carlo():
    st.title("NIFTY 50 Monte Carlo DCF")
    st.caption("Batch intrinsic value screen across the NIFTY 50 constituent universe.")

    st.sidebar.markdown("### Batch Controls")
    forecast_years = st.sidebar.selectbox(
        "Forecast Years",
        [5, 7, 10],
        index=0,
        key="batch_forecast_years",
    )
    simulation_count = st.sidebar.selectbox(
        "Simulations per Company",
        [250, 500, 1000, 2500, 5000],
        index=2,
        key="batch_simulation_count",
    )
    random_seed = st.sidebar.number_input(
        "Random Seed",
        min_value=1,
        max_value=999999,
        value=42,
        step=1,
        key="batch_random_seed",
    )
    selected_companies = st.sidebar.multiselect(
        "Companies",
        list(NIFTY_50_COMPANIES.keys()),
        default=list(NIFTY_50_COMPANIES.keys()),
        key="batch_companies",
    )

    if not selected_companies:
        st.info("Select at least one company to run the batch valuation.")
        return

    st.write(
        f"Ready to run {simulation_count:,} simulations each for "
        f"{len(selected_companies)} companies."
    )

    if not st.button("Run NIFTY 50 Batch Valuation", type="primary"):
        st.info("Use the batch button to start the all-company Monte Carlo DCF run.")
        return

    selected_items = [
        (company, NIFTY_50_COMPANIES[company])
        for company in selected_companies
    ]

    progress = st.progress(0)
    status_line = st.empty()
    started_at = time.perf_counter()
    rows = []

    for index, (company_name, ticker) in enumerate(selected_items, start=1):
        status_line.write(f"Valuing {company_name} ({ticker})...")
        rows.append(
            calculate_company_monte_carlo_summary(
                company_name=company_name,
                ticker=ticker,
                simulation_count=simulation_count,
                forecast_years=forecast_years,
                random_seed=int(random_seed) + index,
            )
        )
        progress.progress(index / len(selected_items))

    runtime_seconds = time.perf_counter() - started_at
    status_line.write(
        f"Completed {len(selected_items)} companies in {runtime_seconds:.1f}s."
    )

    summary_df = pd.DataFrame(rows)
    success_df = summary_df[summary_df["Status"].eq("OK")].copy()
    error_df = summary_df[~summary_df["Status"].eq("OK")].copy()

    if success_df.empty:
        st.error("No companies returned enough financial data for Monte Carlo DCF.")
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
        return

    success_df = success_df.sort_values(
        ["Margin of Safety", "Probability Undervalued"],
        ascending=[False, False],
    )

    top_company = success_df.iloc[0]
    metric_cols = st.columns(4)
    metric_cols[0].metric("Companies Valued", f"{len(success_df)}")
    metric_cols[1].metric("Data Issues", f"{len(error_df)}")
    metric_cols[2].metric(
        "Top Margin of Safety",
        _format_percent(top_company["Margin of Safety"]),
        top_company["Company"],
    )
    metric_cols[3].metric(
        "Top Undervaluation Probability",
        _format_percent(success_df["Probability Undervalued"].max()),
    )

    display_df = success_df.copy()
    for column in [
        "Current Price",
        "Fair Value Mean",
        "Median Value",
        "Bear Case P10",
        "Bull Case P90",
    ]:
        display_df[column] = display_df.apply(
            lambda row: format_money(row[column], row["Currency"], compact=False),
            axis=1,
        )

    for column in [
        "Probability Undervalued",
        "Margin of Safety",
        "Upside to Mean",
        "Revenue Growth Mean",
        "EBIT Margin Mean",
        "WACC Mean",
        "Terminal Growth Mean",
    ]:
        display_df[column] = display_df[column].apply(_format_percent)

    st.markdown("### NIFTY 50 Valuation Ranking")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    chart_df = success_df.head(15).copy()
    chart_df["Margin of Safety %"] = chart_df["Margin of Safety"] * 100.0
    fig = px.bar(
        chart_df,
        x="Margin of Safety %",
        y="Company",
        orientation="h",
        color="Probability Undervalued",
        hover_data=["Ticker", "Current Price", "Fair Value Mean"],
        title="Top Monte Carlo DCF Opportunities",
    )
    fig.update_layout(
        template="plotly_dark",
        yaxis={"categoryorder": "total ascending"},
        height=520,
        margin=dict(l=20, r=20, t=55, b=40),
    )
    st.plotly_chart(fig, use_container_width=True, key="batch_margin_chart")

    if not error_df.empty:
        with st.expander("Companies skipped or partially unavailable"):
            st.dataframe(error_df, use_container_width=True, hide_index=True)

    st.download_button(
        "Download Batch Summary CSV",
        data=success_df.to_csv(index=False).encode("utf-8"),
        file_name="nifty_50_monte_carlo_dcf_summary.csv",
        mime="text/csv",
    )


def _pct_input(
    label,
    value,
    min_value=-50.0,
    max_value=100.0,
    step=0.25,
    key=None,
    container=None,
):
    container = container or st.sidebar
    return (
        container.number_input(
            label,
            min_value=float(min_value),
            max_value=float(max_value),
            value=float(value) * 100.0,
            step=float(step),
            format="%.2f",
            key=key,
        )
        / 100.0
    )


def _number_input(label, value, min_value=0.0, step=1.0, key=None, container=None):
    container = container or st.sidebar
    return container.number_input(
        label,
        min_value=float(min_value),
        value=float(value),
        step=float(step),
        format="%.2f",
        key=key,
    )


def _reset_assumption_state(prefix: str, defaults: dict):
    for key, value in defaults.items():
        st.session_state[f"{prefix}_{key}"] = value


def _format_percent(value):
    if pd.isna(value):
        return "N/A"
    return f"{value:.1%}"


def _report_text(ticker, company_name, currency, stats, probability, scenarios, assumptions):
    buffer = StringIO()
    buffer.write(f"Monte Carlo DCF Valuation Report - {company_name} ({ticker})\n")
    buffer.write("=" * 72 + "\n\n")
    buffer.write(f"Current Price: {format_money(probability['current_price'], currency, compact=False)}\n")
    buffer.write(f"Fair Value Mean: {format_money(probability['fair_value_mean'], currency, compact=False)}\n")
    buffer.write(f"Probability Undervalued: {_format_percent(probability['probability_undervalued'])}\n")
    buffer.write(f"Probability Overvalued: {_format_percent(probability['probability_overvalued'])}\n")
    buffer.write(f"Margin of Safety: {_format_percent(probability['margin_of_safety'])}\n\n")
    buffer.write("Valuation Statistics\n")
    for label in ["mean", "median", "mode", "std_dev", "min", "max", "p5", "p10", "p25", "p50", "p75", "p90", "p95"]:
        buffer.write(f"{label}: {format_money(stats[label], currency, compact=False)}\n")
    buffer.write("\nScenarios\n")
    for _, row in scenarios.iterrows():
        buffer.write(
            f"{row['Scenario']} ({row['Percentile']}): "
            f"{format_money(row['Intrinsic Value'], currency, compact=False)}\n"
        )
    buffer.write("\nAssumptions\n")
    for key, value in assumptions.items():
        buffer.write(f"{key}: {value}\n")
    return buffer.getvalue().encode("utf-8")


def _display_statement_expander(title, statement, currency):
    with st.expander(title):
        if statement is None or statement.empty:
            st.info("No statement data returned by Yahoo Finance.")
        else:
            st.dataframe(statement, use_container_width=True)


def render_monte_carlo_dcf(default_ticker: str = "RELIANCE.NS"):
    st.sidebar.subheader("Monte Carlo DCF")
    scope = st.sidebar.radio(
        "Valuation Scope",
        ["Single Company", "NIFTY 50 Batch"],
        index=0,
        key="mc_scope",
    )

    if scope == "NIFTY 50 Batch":
        render_nifty_50_batch_monte_carlo()
        return

    st.title("Monte Carlo DCF")
    st.caption("Distribution-based intrinsic value engine using Yahoo Finance statements and vectorized NumPy simulations.")

    company_options = ["Custom Ticker"] + list(NIFTY_50_COMPANIES.keys())
    default_company = next(
        (
            company
            for company, symbol in NIFTY_50_COMPANIES.items()
            if symbol == default_ticker
        ),
        "Custom Ticker",
    )
    selected_company = st.sidebar.selectbox(
        "NIFTY 50 Company",
        company_options,
        index=company_options.index(default_company),
        key="mc_company",
    )

    if selected_company == "Custom Ticker":
        ticker = st.sidebar.text_input(
            "Stock Ticker",
            value=default_ticker,
            key="mc_ticker",
        ).strip().upper()
    else:
        ticker = NIFTY_50_COMPANIES[selected_company]
        st.sidebar.caption(ticker)

    if not ticker:
        st.info("Enter a ticker to begin.")
        return

    with st.spinner(f"Loading financial data for {ticker}..."):
        data = load_company_financial_data(ticker)

    baseline = build_baseline_assumptions(
        ticker=ticker,
        info=data["info"],
        fast_info=data["fast_info"],
        financials=data["financials"],
        balance_sheet=data["balance_sheet"],
        cashflow=data["cashflow"],
        current_price=data["current_price"],
    )

    if baseline.base_revenue <= 0:
        st.error("Revenue data was not available from Yahoo Finance, so a DCF cannot be built for this ticker.")
        _display_statement_expander("Income Statement", data["financials"], baseline.currency)
        return

    prefix = f"mc_{ticker.replace('.', '_')}"
    defaults = {
        "revenue_growth_mean": baseline.revenue_growth_mean,
        "revenue_growth_std": baseline.revenue_growth_std,
        "ebit_margin_mean": baseline.ebit_margin_mean,
        "ebit_margin_std": baseline.ebit_margin_std,
        "wacc_mean": baseline.wacc_mean,
        "wacc_std": baseline.wacc_std,
        "terminal_growth_mean": baseline.terminal_growth_mean,
        "terminal_growth_std": baseline.terminal_growth_std,
        "tax_rate": baseline.tax_rate,
        "capex_pct_revenue": baseline.capex_pct_revenue,
        "depreciation_pct_revenue": baseline.depreciation_pct_revenue,
        "working_capital_pct_revenue": baseline.working_capital_pct_revenue,
        "cash": baseline.cash,
        "debt": baseline.debt,
        "shares_outstanding": baseline.shares_outstanding,
    }

    if st.sidebar.button("Reset to Defaults", key=f"{prefix}_reset"):
        _reset_assumption_state(prefix, defaults)

    st.sidebar.markdown("### Simulation Controls")
    forecast_years = st.sidebar.selectbox("Forecast Years", [5, 7, 10], index=0, key=f"{prefix}_forecast_years")
    simulation_count = st.sidebar.selectbox(
        "Simulation Count",
        [1000, 5000, 10000, 25000, 50000],
        index=2,
        key=f"{prefix}_simulation_count",
    )

    st.sidebar.markdown("### Distribution Assumptions")
    assumptions = baseline.to_dict()
    assumptions["revenue_growth_mean"] = _pct_input(
        "Revenue Growth Mean",
        defaults["revenue_growth_mean"],
        min_value=-30.0,
        max_value=60.0,
        key=f"{prefix}_revenue_growth_mean",
    )
    assumptions["revenue_growth_std"] = _pct_input(
        "Revenue Growth Std Dev",
        defaults["revenue_growth_std"],
        min_value=0.0,
        max_value=40.0,
        key=f"{prefix}_revenue_growth_std",
    )
    assumptions["ebit_margin_mean"] = _pct_input(
        "EBIT Margin Mean",
        defaults["ebit_margin_mean"],
        min_value=-20.0,
        max_value=65.0,
        key=f"{prefix}_ebit_margin_mean",
    )
    assumptions["ebit_margin_std"] = _pct_input(
        "EBIT Margin Std Dev",
        defaults["ebit_margin_std"],
        min_value=0.0,
        max_value=30.0,
        key=f"{prefix}_ebit_margin_std",
    )
    assumptions["wacc_mean"] = _pct_input(
        "WACC Mean",
        defaults["wacc_mean"],
        min_value=2.5,
        max_value=35.0,
        key=f"{prefix}_wacc_mean",
    )
    assumptions["wacc_std"] = _pct_input(
        "WACC Std Dev",
        defaults["wacc_std"],
        min_value=0.0,
        max_value=15.0,
        key=f"{prefix}_wacc_std",
    )
    assumptions["terminal_growth_mean"] = _pct_input(
        "Terminal Growth Mean",
        defaults["terminal_growth_mean"],
        min_value=-3.0,
        max_value=8.0,
        key=f"{prefix}_terminal_growth_mean",
    )
    assumptions["terminal_growth_std"] = _pct_input(
        "Terminal Growth Std Dev",
        defaults["terminal_growth_std"],
        min_value=0.0,
        max_value=5.0,
        key=f"{prefix}_terminal_growth_std",
    )

    with st.sidebar.expander("Advanced DCF Assumptions") as advanced:
        assumptions["tax_rate"] = _pct_input(
            "Tax Rate",
            defaults["tax_rate"],
            min_value=0.0,
            max_value=50.0,
            key=f"{prefix}_tax_rate",
            container=advanced,
        )
        assumptions["capex_pct_revenue"] = _pct_input(
            "CapEx / Revenue",
            defaults["capex_pct_revenue"],
            min_value=0.0,
            max_value=50.0,
            key=f"{prefix}_capex_pct_revenue",
            container=advanced,
        )
        assumptions["depreciation_pct_revenue"] = _pct_input(
            "Depreciation / Revenue",
            defaults["depreciation_pct_revenue"],
            min_value=0.0,
            max_value=40.0,
            key=f"{prefix}_depreciation_pct_revenue",
            container=advanced,
        )
        assumptions["working_capital_pct_revenue"] = _pct_input(
            "Working Capital / Revenue",
            defaults["working_capital_pct_revenue"],
            min_value=-30.0,
            max_value=50.0,
            key=f"{prefix}_working_capital_pct_revenue",
            container=advanced,
        )
        assumptions["cash"] = _number_input("Cash", defaults["cash"], key=f"{prefix}_cash", container=advanced)
        assumptions["debt"] = _number_input("Debt", defaults["debt"], key=f"{prefix}_debt", container=advanced)
        assumptions["shares_outstanding"] = _number_input(
            "Shares Outstanding",
            defaults["shares_outstanding"],
            min_value=1.0,
            step=1000000.0,
            key=f"{prefix}_shares_outstanding",
            container=advanced,
        )

    assumptions["terminal_growth_mean"] = min(
        assumptions["terminal_growth_mean"],
        assumptions["wacc_mean"] - 0.005,
    )

    started_at = time.perf_counter()
    results = run_monte_carlo_dcf(
        assumptions=assumptions,
        simulation_count=simulation_count,
        forecast_years=forecast_years,
    )
    runtime_seconds = time.perf_counter() - started_at

    stats = valuation_statistics(results)
    probability = probability_analysis(results, assumptions["current_price"])
    scenarios = scenario_analysis(stats)
    tornado = tornado_analysis(assumptions, forecast_years)

    baseline_dcf = calculate_dcf(
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
    )
    forecast_schedule = forecast_dcf_schedule(
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
    )

    currency = assumptions["currency"]

    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Current Price", format_money(probability["current_price"], currency, compact=False))
    top2.metric("Fair Value Mean", format_money(probability["fair_value_mean"], currency, compact=False))
    top3.metric("Probability Undervalued", _format_percent(probability["probability_undervalued"]))
    top4.metric("Margin of Safety", _format_percent(probability["margin_of_safety"]))

    st.caption(
        f"{simulation_count:,} simulations completed in {runtime_seconds:.3f}s for "
        f"{baseline.company_name} ({ticker})."
    )

    st.markdown("### Scenario Analysis")
    scenario_cols = st.columns(3)
    for column, (_, row) in zip(scenario_cols, scenarios.iterrows()):
        column.metric(
            row["Scenario"],
            format_money(row["Intrinsic Value"], currency, compact=False),
            row["Percentile"],
        )

    st.markdown("### Baseline DCF")
    dcf_cols = st.columns(3)
    dcf_cols[0].metric("Enterprise Value", format_money(baseline_dcf["enterprise_value"], currency))
    dcf_cols[1].metric("Equity Value", format_money(baseline_dcf["equity_value"], currency))
    dcf_cols[2].metric(
        "Intrinsic Value / Share",
        format_money(baseline_dcf["intrinsic_value_per_share"], currency, compact=False),
    )

    chart_tab, stats_tab, dcf_tab, statements_tab, export_tab = st.tabs(
        ["Charts", "Statistics", "DCF Model", "Financial Statements", "Exports"]
    )

    with chart_tab:
        st.plotly_chart(
            create_intrinsic_value_histogram(results, stats, probability["current_price"]),
            use_container_width=True,
            key=f"{prefix}_histogram",
        )
        col_a, col_b = st.columns(2)
        col_a.plotly_chart(
            create_probability_density_chart(results, stats, probability["current_price"]),
            use_container_width=True,
            key=f"{prefix}_density",
        )
        cdf_target = col_b.number_input(
            "CDF Target Value",
            min_value=0.0,
            value=float(probability["current_price"] or stats["mean"]),
            step=max(float(stats["std_dev"]) / 20.0, 1.0),
            format="%.2f",
            key=f"{prefix}_cdf_target",
        )
        probability_below_target = (
            results["intrinsic_value_per_share"] <= cdf_target
        ).mean()
        col_b.metric(
            "Probability Below Target",
            _format_percent(probability_below_target),
            format_money(cdf_target, currency, compact=False),
        )
        col_b.plotly_chart(
            create_cumulative_distribution_chart(results, probability["current_price"]),
            use_container_width=True,
            key=f"{prefix}_cdf",
        )
        st.plotly_chart(
            create_tornado_chart(tornado),
            use_container_width=True,
            key=f"{prefix}_tornado",
        )

    with stats_tab:
        stat_rows = [
            ("Mean Intrinsic Value", stats["mean"]),
            ("Median Intrinsic Value", stats["median"]),
            ("Mode Intrinsic Value", stats["mode"]),
            ("Standard Deviation", stats["std_dev"]),
            ("Minimum Value", stats["min"]),
            ("Maximum Value", stats["max"]),
            ("5th Percentile", stats["p5"]),
            ("10th Percentile", stats["p10"]),
            ("25th Percentile", stats["p25"]),
            ("50th Percentile", stats["p50"]),
            ("75th Percentile", stats["p75"]),
            ("90th Percentile", stats["p90"]),
            ("95th Percentile", stats["p95"]),
        ]
        stats_df = pd.DataFrame(stat_rows, columns=["Metric", "Value"])
        stats_df["Formatted Value"] = stats_df["Value"].apply(lambda value: format_money(value, currency, compact=False))
        st.dataframe(stats_df, use_container_width=True, hide_index=True)

        prob_cols = st.columns(4)
        prob_cols[0].metric("Current Price", format_money(probability["current_price"], currency, compact=False))
        prob_cols[1].metric("Fair Value Mean", format_money(probability["fair_value_mean"], currency, compact=False))
        prob_cols[2].metric("Probability Overvalued", _format_percent(probability["probability_overvalued"]))
        prob_cols[3].metric("Probability Undervalued", _format_percent(probability["probability_undervalued"]))

    with dcf_tab:
        display_schedule = forecast_schedule.copy()
        money_columns = [col for col in display_schedule.columns if col != "Year"]
        for column in money_columns:
            display_schedule[column] = display_schedule[column].apply(
                lambda value: "" if pd.isna(value) else format_money(value, currency)
            )
        st.dataframe(display_schedule, use_container_width=True, hide_index=True)

        assumptions_df = pd.DataFrame(
            [
                ("Revenue Growth Mean", assumptions["revenue_growth_mean"]),
                ("Revenue Growth Std Dev", assumptions["revenue_growth_std"]),
                ("EBIT Margin Mean", assumptions["ebit_margin_mean"]),
                ("EBIT Margin Std Dev", assumptions["ebit_margin_std"]),
                ("Tax Rate", assumptions["tax_rate"]),
                ("CapEx / Revenue", assumptions["capex_pct_revenue"]),
                ("Depreciation / Revenue", assumptions["depreciation_pct_revenue"]),
                ("Working Capital / Revenue", assumptions["working_capital_pct_revenue"]),
                ("WACC Mean", assumptions["wacc_mean"]),
                ("WACC Std Dev", assumptions["wacc_std"]),
                ("Terminal Growth Mean", assumptions["terminal_growth_mean"]),
                ("Terminal Growth Std Dev", assumptions["terminal_growth_std"]),
            ],
            columns=["Assumption", "Value"],
        )
        assumptions_df["Value"] = assumptions_df["Value"].apply(lambda value: f"{value:.2%}")
        st.dataframe(assumptions_df, use_container_width=True, hide_index=True)

    with statements_tab:
        _display_statement_expander("Annual Income Statement", data["financials"], currency)
        _display_statement_expander("Annual Balance Sheet", data["balance_sheet"], currency)
        _display_statement_expander("Annual Cash Flow Statement", data["cashflow"], currency)
        _display_statement_expander("Quarterly Income Statement", data["quarterly_financials"], currency)
        _display_statement_expander("Quarterly Balance Sheet", data["quarterly_balance_sheet"], currency)
        _display_statement_expander("Quarterly Cash Flow Statement", data["quarterly_cashflow"], currency)

    with export_tab:
        export_assumptions = pd.DataFrame(
            [{"Assumption": key, "Value": value} for key, value in assumptions.items()]
        )
        summary_export = pd.DataFrame(
            [{"Metric": key, "Value": value} for key, value in {**stats, **probability}.items()]
        )
        report = _report_text(ticker, baseline.company_name, currency, stats, probability, scenarios, assumptions)

        dl1, dl2, dl3, dl4 = st.columns(4)
        dl1.download_button(
            "Simulation Results CSV",
            data=results.to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_monte_carlo_dcf_simulations.csv",
            mime="text/csv",
        )
        dl2.download_button(
            "Summary Statistics CSV",
            data=summary_export.to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_monte_carlo_dcf_summary.csv",
            mime="text/csv",
        )
        dl3.download_button(
            "DCF Assumptions CSV",
            data=export_assumptions.to_csv(index=False).encode("utf-8"),
            file_name=f"{ticker}_monte_carlo_dcf_assumptions.csv",
            mime="text/csv",
        )
        dl4.download_button(
            "Valuation Report",
            data=report,
            file_name=f"{ticker}_monte_carlo_dcf_report.txt",
            mime="text/plain",
        )


if __name__ == "__main__":
    st.set_page_config(page_title="Monte Carlo DCF", layout="wide")
    render_monte_carlo_dcf()
