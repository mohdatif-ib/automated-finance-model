from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go


def _valuation_series(results: pd.DataFrame) -> pd.Series:
    return results["intrinsic_value_per_share"].replace([np.inf, -np.inf], np.nan).dropna()


def _add_reference_line(fig, x_value, label, color, dash="dash"):
    if x_value is None or not np.isfinite(x_value):
        return

    fig.add_vline(
        x=float(x_value),
        line_width=2,
        line_dash=dash,
        line_color=color,
        annotation_text=label,
        annotation_position="top",
    )


def create_intrinsic_value_histogram(results, stats, current_price=None):
    values = _valuation_series(results)
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=values,
            nbinsx=70,
            marker_color="#2dd4bf",
            opacity=0.75,
            name="Intrinsic Value",
        )
    )
    _add_reference_line(fig, stats.get("mean"), "Mean", "#fbbf24")
    _add_reference_line(fig, stats.get("median"), "Median", "#60a5fa")
    _add_reference_line(fig, stats.get("mode"), "Mode", "#a78bfa")
    _add_reference_line(fig, current_price, "Market Price", "#f87171", "solid")
    fig.update_layout(
        template="plotly_dark",
        title="Monte Carlo Intrinsic Value Distribution",
        xaxis_title="Intrinsic Value Per Share",
        yaxis_title="Simulation Count",
        bargap=0.03,
        height=460,
        margin=dict(l=20, r=20, t=55, b=40),
    )
    return fig


def create_probability_density_chart(results, stats=None, current_price=None):
    values = _valuation_series(results)
    x_min, x_max = np.percentile(values, [1, 99])
    x_grid = np.linspace(x_min, x_max, 300)

    try:
        from scipy.stats import gaussian_kde

        kde = gaussian_kde(values)
        density = kde(x_grid)
    except Exception:
        counts, edges = np.histogram(values, bins=80, density=True)
        centers = (edges[:-1] + edges[1:]) / 2.0
        density = np.interp(x_grid, centers, counts)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=x_grid,
            y=density,
            mode="lines",
            fill="tozeroy",
            line=dict(color="#38bdf8", width=3),
            name="Density",
        )
    )
    if stats:
        _add_reference_line(fig, stats.get("mean"), "Mean", "#fbbf24")
    _add_reference_line(fig, current_price, "Market Price", "#f87171", "solid")
    fig.update_layout(
        template="plotly_dark",
        title="Probability Density Distribution",
        xaxis_title="Intrinsic Value Per Share",
        yaxis_title="Probability Density",
        height=430,
        margin=dict(l=20, r=20, t=55, b=40),
    )
    return fig


def create_cumulative_distribution_chart(results, current_price=None):
    values = np.sort(_valuation_series(results).to_numpy())
    cumulative_probability = np.arange(1, len(values) + 1) / len(values)

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=values,
            y=cumulative_probability,
            mode="lines",
            line=dict(color="#34d399", width=3),
            name="Cumulative Probability",
        )
    )
    _add_reference_line(fig, current_price, "Market Price", "#f87171", "solid")
    fig.update_layout(
        template="plotly_dark",
        title="Cumulative Valuation Distribution",
        xaxis_title="Intrinsic Value Per Share",
        yaxis_title="Probability Valuation Is Below X",
        yaxis_tickformat=".0%",
        height=430,
        margin=dict(l=20, r=20, t=55, b=40),
    )
    return fig


def create_tornado_chart(tornado_df):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=tornado_df["Variable"],
            x=tornado_df["Impact"],
            orientation="h",
            marker_color="#fb7185",
            customdata=np.stack(
                [
                    tornado_df["Low Case"],
                    tornado_df["High Case"],
                    tornado_df["Base Value"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Impact: %{x:,.2f}<br>"
                "Low Case: %{customdata[0]:,.2f}<br>"
                "High Case: %{customdata[1]:,.2f}<br>"
                "Base: %{customdata[2]:,.2f}<extra></extra>"
            ),
            name="Valuation Impact",
        )
    )
    fig.update_layout(
        template="plotly_dark",
        title="Tornado Sensitivity Chart",
        xaxis_title="Absolute Impact on Intrinsic Value Per Share",
        yaxis_title="",
        height=390,
        margin=dict(l=20, r=20, t=55, b=40),
    )
    return fig

