import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from modules.financial_statements import fetch_financials

financials = fetch_financials("RELIANCE.NS")

print(financials["income_statement"])

# Download weekly data
reliance = yf.download(
    "RELIANCE.NS",
    start="2024-05-19",
    end="2026-05-17",
    interval="1wk"
)

nifty = yf.download(
    "^NSEI",
    start="2024-05-19",
    end="2026-05-17",
    interval="1wk"
)

# Keep close prices
reliance = reliance[["Close"]]
nifty = nifty[["Close"]]

# Rename columns
reliance.columns = ["Reliance"]
nifty.columns = ["Nifty"]

# Merge datasets
df = pd.merge(
    reliance,
    nifty,
    left_index=True,
    right_index=True
)

# Calculate returns
df["Reliance_Returns"] = df["Reliance"].pct_change()

df["Nifty_Returns"] = df["Nifty"].pct_change()

# Remove missing rows
df = df.dropna()

# Beta calculation
covariance = np.cov(
    df["Reliance_Returns"],
    df["Nifty_Returns"]
)[0][1]

variance = np.var(df["Nifty_Returns"])

beta = covariance / variance

print(f"Beta: {beta:.2f}")

# CAPM Assumptions
risk_free_rate = 0.07
market_return = 0.12

# Regression Beta

X = sm.add_constant(df["Nifty_Returns"])

model = sm.OLS(
    df["Reliance_Returns"],
    X
).fit()

print(model.summary())

# Regression Line Plot

plt.figure(figsize=(8,6))

plt.scatter(
    df["Nifty_Returns"],
    df["Reliance_Returns"],
    alpha=0.7
)

# Regression line
x_vals = df["Nifty_Returns"]

y_vals = (
    model.params[0]
    + model.params[1] * x_vals
)

plt.plot(x_vals, y_vals)

plt.title("Reliance vs NIFTY Regression")

plt.xlabel("NIFTY Returns")

plt.ylabel("Reliance Returns")

plt.show()

# Cost of Equity
cost_of_equity = (
    risk_free_rate
    + beta * (market_return - risk_free_rate)
)

print(f"Cost of Equity: {cost_of_equity:.2%}")

# -----------------------------
# WACC CALCULATION
# -----------------------------

# Assumptions
cost_of_debt = 0.08
tax_rate = 0.25

# Market values (example assumptions)
equity_value = 20000000000000
debt_value = 3500000000000

# Total capital
total_value = equity_value + debt_value

# Capital structure weights
equity_weight = equity_value / total_value
debt_weight = debt_value / total_value

# After-tax cost of debt
after_tax_debt = cost_of_debt * (1 - tax_rate)

# WACC
wacc = (
    equity_weight * cost_of_equity
    + debt_weight * after_tax_debt
)

print(f"WACC: {wacc:.2%}")

# -----------------------------
# DCF MODEL
# -----------------------------

# Base assumptions
base_revenue = 1000000

revenue_growth = 0.10

ebit_margin = 0.22

tax_rate = 0.25

capex_percent = 0.05

working_capital_percent = 0.03

forecast_years = 5

# Store forecasts
revenues = []

fcfs = []

# Forecast loop
current_revenue = base_revenue

for year in range(1, forecast_years + 1):

    current_revenue = current_revenue * (1 + revenue_growth)

    revenues.append(current_revenue)

    # EBIT
    ebit = current_revenue * ebit_margin

    # NOPAT
    nopat = ebit * (1 - tax_rate)

    # Capex
    capex = current_revenue * capex_percent

    # Working capital
    wc = current_revenue * working_capital_percent

    # Free cash flow
    fcf = nopat - capex - wc

    fcfs.append(fcf)

# Print forecasts
print("Projected Revenues:")
print(revenues)

print("Projected FCFs:")
print(fcfs)

# Discount FCFs
discounted_fcfs = []

for i, fcf in enumerate(fcfs, start=1):

    pv = fcf / ((1 + wacc) ** i)

    discounted_fcfs.append(pv)

enterprise_value = sum(discounted_fcfs)

print(f"Enterprise Value: {enterprise_value:,.2f}")

# Terminal Value

terminal_growth = 0.04

terminal_fcf = fcfs[-1] * (1 + terminal_growth)

terminal_value = (
    terminal_fcf /
    (wacc - terminal_growth)
)

discounted_terminal = (
    terminal_value /
    ((1 + wacc) ** forecast_years)
)

enterprise_value += discounted_terminal

print(f"DCF Enterprise Value: {enterprise_value:,.2f}")

# -----------------------------
# DCF SUMMARY TABLE
# -----------------------------

dcf_df = pd.DataFrame({
    "Year": range(1, forecast_years + 1),
    "Revenue": revenues,
    "FCF": fcfs,
    "Discounted FCF": discounted_fcfs
})

print(dcf_df)

# -----------------------------
# DCF VISUALIZATION
# -----------------------------

plt.figure(figsize=(10,6))

plt.plot(
    dcf_df["Year"],
    dcf_df["Revenue"],
    marker="o",
    label="Revenue"
)

plt.plot(
    dcf_df["Year"],
    dcf_df["FCF"],
    marker="o",
    label="Free Cash Flow"
)

plt.title("DCF Forecast")

plt.xlabel("Year")

plt.ylabel("Value")

plt.legend()

plt.show()

# Scatter plot
plt.figure(figsize=(8,6))

plt.scatter(
    df["Nifty_Returns"],
    df["Reliance_Returns"]
)

plt.title("Reliance vs NIFTY Returns")

plt.xlabel("NIFTY Returns")

plt.ylabel("Reliance Returns")

plt.show()

# -----------------------------
# EXPORT TO EXCEL
# -----------------------------

with pd.ExcelWriter(
    "Reliance_Valuation_Model.xlsx",
    engine="xlsxwriter"
) as writer:

    # Historical data
    df.to_excel(
        writer,
        sheet_name="Historical_Data"
    )

    # DCF forecast
    dcf_df.to_excel(
        writer,
        sheet_name="DCF_Model",
        index=False
    )

print("Excel valuation model exported.")