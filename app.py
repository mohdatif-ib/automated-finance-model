# app.py
# RUN:
# streamlit run app.py

import streamlit as st
import yfinance as yf
from modules.charts import create_candlestick_chart
from modules.indicators import add_indicators
from styles import load_css
import importlib
import math
from numbers import Number
import plotly.express as px
import pandas as pd
import utils as finance_utils
from pages.monte_carlo_dcf import render_monte_carlo_dcf


finance_utils = importlib.reload(finance_utils)


try:
    format_money = finance_utils.format_money
    get_currency_symbol = finance_utils.get_currency_symbol
    format_large_numbers = finance_utils.format_large_numbers
except AttributeError:
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

    def format_money(num, currency="INR", compact=True):
        if not isinstance(num, Number) or isinstance(num, bool) or not math.isfinite(num):
            return "N/A"

        symbol = get_currency_symbol(currency)

        if not compact:
            return f"{symbol}{num:,.2f}"

        for value, suffix in [
            (1e12, "T"),
            (1e9, "B"),
            (1e6, "M"),
            (1e3, "K"),
        ]:
            if abs(num) >= value:
                return f"{symbol}{num / value:.2f} {suffix}"

        return f"{symbol}{num:.2f}"

    def format_large_numbers(df, currency="INR"):
        formatted_df = df.copy()

        for col in formatted_df.columns:
            formatted_df[col] = formatted_df[col].apply(
                lambda value: format_money(value, currency)
            )

        return formatted_df


@st.cache_data(ttl=3600)
def get_stock_data(ticker):
        return yf.Ticker(ticker)


def get_market_benchmark(ticker):
    indian_ticker = ticker == "^NSEI" or ticker.endswith((".NS", ".BO"))

    if indian_ticker:
        return "^NSEI", "NIFTY 50"

    return "^GSPC", "S&P 500"


def get_close_series(price_data):
    if price_data is None or price_data.empty:
        return pd.Series(dtype="float64")

    if isinstance(price_data.columns, pd.MultiIndex):
        if "Close" not in price_data.columns.get_level_values(0):
            return pd.Series(dtype="float64")
        close = price_data["Close"]
        if isinstance(close, pd.DataFrame):
            close = close.iloc[:, 0]
        return close.dropna()

    if "Close" not in price_data.columns:
        return pd.Series(dtype="float64")

    return price_data["Close"].dropna()


def is_valid_number(value):
    return (
        isinstance(value, Number)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def to_number(value):
    try:
        numeric_value = pd.to_numeric(value)
    except Exception:
        return None

    if is_valid_number(numeric_value):
        return float(numeric_value)

    return None


def get_first_value(sources, keys):
    for source in sources:
        if not source:
            continue

        for key in keys:
            try:
                if hasattr(source, "get"):
                    value = source.get(key)
                else:
                    value = source[key]
            except Exception:
                continue

            if value is None:
                continue

            try:
                if pd.isna(value):
                    continue
            except Exception:
                pass

            if is_valid_number(value) and value == 0:
                continue

            if str(value).strip():
                return value

    return None


def get_latest_statement_value(statement, row_names):
    if statement is None or statement.empty:
        return None

    for row_name in row_names:
        if row_name in statement.index:
            values = pd.to_numeric(
                statement.loc[row_name],
                errors="coerce"
            ).dropna()

            if not values.empty:
                return float(values.iloc[0])

    return None


def normalize_dividend_yield(value):
    value = to_number(value)

    if not is_valid_number(value):
        return None

    if value > 1:
        return value / 100

    return value


def get_recent_dividend_yield(stock, current_price):
    if not is_valid_number(current_price) or current_price <= 0:
        return None

    try:
        dividends = stock.dividends
    except Exception:
        return None

    if dividends is None or dividends.empty:
        return None

    try:
        cutoff = dividends.index.max() - pd.DateOffset(years=1)
        recent_dividends = dividends[dividends.index >= cutoff]
        annual_dividend = recent_dividends.sum()
    except Exception:
        annual_dividend = dividends.tail(4).sum()

    if not is_valid_number(annual_dividend) or annual_dividend <= 0:
        return None

    return annual_dividend / current_price


def normalize_to_dates(series):
    normalized = series.copy()
    normalized.index = (
        pd.DatetimeIndex(normalized.index)
        .tz_localize(None)
        .normalize()
    )
    return normalized


def get_statement_scale(currency):
    currency = (currency or "").upper()

    if currency == "INR":
        return 1e7, f"{get_currency_symbol(currency)} Cr"

    return 1e9, f"{get_currency_symbol(currency)} B"

# ---------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------

st.set_page_config(
    page_title="Equity Research Dashboard",
    page_icon="📈",
    layout="wide"
)

load_css()

# ---------------------------------------------------
# CUSTOM CSS
# ---------------------------------------------------

st.markdown("""
<style>

.main {
    background-color: #0E1117;
}

.stMetric {
    background-color: #1E1E1E;
    padding: 15px;
    border-radius: 12px;
    border: 1px solid #333;
}

div[data-testid="stExpander"] {
    border: 1px solid #333;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

st.sidebar.title("📊 Dashboard Settings")

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Monte Carlo DCF"],
    index=0
)

if page == "Monte Carlo DCF":
    render_monte_carlo_dcf(default_ticker="RELIANCE.NS")
    st.stop()

company_dict = {
    "NIFTY 50": "^NSEI",
    "Reliance Industries": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "State Bank of India": "SBIN.NS",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN"
}

company = st.sidebar.selectbox(
    "Select Company",
    list(company_dict.keys())
)

ticker = company_dict[company]
benchmark_ticker, benchmark_name = get_market_benchmark(ticker)

period = st.sidebar.selectbox(
    "Select Time Period",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)

interval = st.sidebar.selectbox(
    "Price Interval",
    ["1d", "1wk", "1mo"],
    index=0
)

show_volume = st.sidebar.checkbox(
    "Show Volume",
    value=True
)

# ---------------------------------------------------
# FETCH DATA
# ---------------------------------------------------

stock = yf.Ticker(ticker)

hist = stock.history(
    period=period,
    interval=interval
)

if hist.empty:
    st.error(
        f"No price data returned for {company} ({ticker}). Try another ticker or time period."
    )
    st.stop()

# ------------------------------
# CALCULATED BETA VS MARKET BENCHMARK
# ------------------------------

try:

    benchmark_data = yf.download(
        benchmark_ticker,
        period="2y",
        auto_adjust=True,
        progress=False
    )

    stock_beta_data = yf.download(
        ticker,
        period="2y",
        auto_adjust=True,
        progress=False
    )

    stock_returns = normalize_to_dates(
        get_close_series(stock_beta_data)
    ).pct_change().dropna()

    benchmark_returns = normalize_to_dates(
        get_close_series(benchmark_data)
    ).pct_change().dropna()

    beta_df = pd.concat(
        [stock_returns, benchmark_returns],
        axis=1
    ).dropna()

    if beta_df.empty:
        raise ValueError("No overlapping return dates")

    beta_df.columns = [
        "Stock",
        "Market"
    ]

    beta = (
        beta_df.cov().iloc[0, 1]
        /
        beta_df["Market"].var()
    )

except:
    beta = None
try:
    info = stock.info
except:
    info = {}

try:
    fast_info = stock.fast_info
except:
    fast_info = {}

currency = get_first_value(
    [info, fast_info],
    ["currency"]
) or (
    "INR" if ticker.endswith((".NS", ".BO")) or ticker == "^NSEI" else "USD"
)

statement_divisor, statement_unit = get_statement_scale(currency)

financials = stock.financials

balance_sheet = stock.balance_sheet

cashflow = stock.cashflow

news = stock.news

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("📈 Equity Research Dashboard")

st.caption(
    f"Live market analysis for {company}"
)

# ---------------------------------------------------
# TABS
# ---------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Overview",
    "Financials",
    "DCF Valuation",
    "News",
    "Historical Prices"
])

# ===================================================
# OVERVIEW TAB
# ===================================================

with tab1:

    st.subheader(f"{company} ({ticker})")

    # ------------------------------
    # METRICS
    # ------------------------------

    try:
        current_price = hist["Close"].iloc[-1]
    except:
        current_price = 0

    market_cap = get_first_value(
        [info, fast_info],
        ["marketCap", "market_cap"]
    )
    market_cap = to_number(market_cap)

    shares_outstanding = get_first_value(
        [info, fast_info],
        ["sharesOutstanding", "shares"]
    )
    shares_outstanding = to_number(shares_outstanding)

    if not is_valid_number(market_cap) and is_valid_number(shares_outstanding):
        market_cap = shares_outstanding * current_price

    pe_ratio = get_first_value(
        [info],
        ["trailingPE", "forwardPE"]
    )
    pe_ratio = to_number(pe_ratio)

    if not is_valid_number(pe_ratio) and is_valid_number(market_cap):
        latest_net_income = get_latest_statement_value(
            financials,
            ["Net Income", "Net Income Common Stockholders"]
        )

        if is_valid_number(latest_net_income) and latest_net_income > 0:
            pe_ratio = market_cap / latest_net_income

    dividend_yield = normalize_dividend_yield(
        get_first_value(
            [info, fast_info],
            [
                "dividendYield",
                "trailingAnnualDividendYield",
                "yield"
            ]
        )
    )

    if dividend_yield is None:
        dividend_yield = get_recent_dividend_yield(
            stock,
            current_price
        )
    
    market_cap_display = (
        format_money(market_cap, currency)
        if market_cap
        else "N/A"
    )

    pe_display = (
    f"{pe_ratio:.2f}"
    if pe_ratio
    else "N/A"
)

    dividend_display = (
    f"{dividend_yield*100:.2f}%"
    if dividend_yield
    else "N/A"
)

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Current Price",
        format_money(current_price, currency, compact=False)
    )

    col2.metric(
    "Market Cap",
    market_cap_display
)

    col3.metric(
    "P/E Ratio",
    pe_display
)

    col4.metric(
    "Dividend Yield",
    dividend_display
)

    col5.metric(
    "Beta",
    f"{beta:.2f}" if beta is not None else "N/A"
    )


    hist = add_indicators(hist)

    fig = create_candlestick_chart(
    hist,
    show_volume=show_volume,
    show_sma=True
    )

    st.plotly_chart(
    fig,
    use_container_width=True,
    key="main_chart"
    )

    st.subheader(f"📊 Performance vs {benchmark_name}")
    
    benchmark_stock = yf.Ticker(benchmark_ticker)
    
    benchmark_hist = benchmark_stock.history(period=period)
    
    stock_close = normalize_to_dates(hist["Close"])
    benchmark_close = normalize_to_dates(get_close_series(benchmark_hist))
    
    comparison = pd.concat(
        [stock_close, benchmark_close],
        axis=1
    ).dropna()

    comparison.columns = [company, benchmark_name]
    
    if not comparison.empty:
        comparison = comparison / comparison.iloc[0] * 100
    
        fig = px.line(
            comparison,
            title=f"{company} vs {benchmark_name} (Base = 100)"
        )
    
        fig.update_layout(
            template="plotly_dark",
            height=500
        )
    
        st.plotly_chart(
            fig,
            use_container_width=True
        )
    else:
        st.info(
            f"Performance comparison unavailable because {company} and {benchmark_name} have no overlapping dates."
        )
    # ------------------------------
    # RETURNS
    # ------------------------------

    hist["Returns"] = hist["Close"].pct_change()

    total_return = (
        (hist["Close"].iloc[-1]
         / hist["Close"].iloc[0]) - 1
    ) * 100

    volatility = (
        hist["Returns"].std()
        * (252 ** 0.5)
    ) * 100

    col6, col7 = st.columns(2)

    col6.metric(
        "Total Return",
        f"{total_return:.2f}%"
    )

    col7.metric(
        "Annualized Volatility",
        f"{volatility:.2f}%"
    )
    
    try:
        benchmark_return = (
            (benchmark_close.iloc[-1] /
             benchmark_close.iloc[0]) - 1
        ) * 100
    except:
        benchmark_return = None
    
    col8, col9 = st.columns(2)
    
    col8.metric(
        "Stock Return",
        f"{total_return:.2f}%"
    )
    
    col9.metric(
        f"{benchmark_name} Return",
        f"{benchmark_return:.2f}%" if benchmark_return is not None else "N/A"
    )
    # ------------------------------
    # BUSINESS SUMMARY
    # ------------------------------

    st.subheader("🏢 Company Overview")

    st.write(
        info.get(
            "longBusinessSummary",
            "No company description available."
        )
    )

# ===================================================
# FINANCIALS TAB
# ===================================================

with tab2:

    st.subheader("📄 Financial Statements")

    # ------------------------------------------------
    # INCOME STATEMENT
    # ------------------------------------------------

    with st.expander(
        "Income Statement",
        expanded=True
    ):

        try:

            income_metrics = [
                "Total Revenue",
                "Gross Profit",
                "Operating Income",
                "EBITDA",
                "Net Income"
            ]

            income_display = financials.loc[
                financials.index.intersection(
                    income_metrics
                )
            ]

            # ==========================================
            # REVENUE CHART
            # ==========================================

            if "Total Revenue" in financials.index:

                st.markdown(
                    "### Revenue Trend"
                )

                revenue = financials.loc[
                    "Total Revenue"
                ]

                revenue_df = (
                    revenue
                    .reset_index()
                )

                revenue_df.columns = [
                    "Date",
                    "Revenue"
                ]

                # Scale statement values for the selected listing currency.

                revenue_df["Revenue"] = (
                    revenue_df["Revenue"]
                    / statement_divisor
                )

                fig = px.line(
                    revenue_df,
                    x="Date",
                    y="Revenue",
                    markers=True
                )

                fig.update_layout(
                    template="plotly_dark",

                    height=400,

                    title="Revenue Trend",

                    title_x=0.02,

                    xaxis_title="Year",

                    yaxis_title=f"Revenue ({statement_unit})",

                    margin=dict(
                        l=20,
                        r=20,
                        t=50,
                        b=20
                    )
                )

                fig.update_traces(
                    line=dict(width=3)
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="revenue_chart"
                )

            # ==========================================
            # NET INCOME CHART
            # ==========================================

            if "Net Income" in financials.index:

                st.markdown(
                    "### Net Income Trend"
                )

                net_income = financials.loc[
                    "Net Income"
                ]

                net_income_df = (
                    net_income
                    .reset_index()
                )

                net_income_df.columns = [
                    "Date",
                    "Net Income"
                ]

                # Convert to Crores

                net_income_df["Net Income"] = (
                    net_income_df["Net Income"]
                    / statement_divisor
                )

                fig = px.line(
                    net_income_df,
                    x="Date",
                    y="Net Income",
                    markers=True
                )

                fig.update_layout(
                    template="plotly_dark",

                    height=400,

                    title="Net Income Trend",

                    title_x=0.02,

                    xaxis_title="Year",

                    yaxis_title=f"Net Income ({statement_unit})",

                    margin=dict(
                        l=20,
                        r=20,
                        t=50,
                        b=20
                    )
                )

                fig.update_traces(
                    line=dict(width=3)
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="net_income_chart"
                )

            # ==========================================
            # TABLE
            # ==========================================

            st.markdown("### Key Metrics")

            st.dataframe(
                format_large_numbers(
                    income_display.T,
                    currency
                ),
                use_container_width=True
            )

        except Exception as e:

            st.warning(
                "Income statement unavailable"
            )

            st.code(str(e))

    # ------------------------------------------------
    # BALANCE SHEET
    # ------------------------------------------------

    with st.expander("Balance Sheet"):

        try:

            balance_metrics = [
                "Total Assets",
                "Total Debt",
                "Cash And Cash Equivalents",
                "Stockholders Equity"
            ]

            balance_display = balance_sheet.loc[
                balance_sheet.index.intersection(
                    balance_metrics
                )
            ]

            # ==========================================
            # ASSETS CHART
            # ==========================================

            if "Total Assets" in balance_sheet.index:

                st.markdown(
                    "### Total Assets Trend"
                )

                assets = balance_sheet.loc[
                    "Total Assets"
                ]

                assets_df = (
                    assets
                    .reset_index()
                )

                assets_df.columns = [
                    "Date",
                    "Assets"
                ]

                assets_df["Assets"] = (
                    assets_df["Assets"]
                    / statement_divisor
                )

                fig = px.line(
                    assets_df,
                    x="Date",
                    y="Assets",
                    markers=True
                )

                fig.update_layout(
                    template="plotly_dark",

                    height=400,

                    title="Assets Trend",

                    title_x=0.02,

                    xaxis_title="Year",

                    yaxis_title=f"Assets ({statement_unit})"
                )

                fig.update_traces(
                    line=dict(width=3)
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="assets_chart"
                )

            # ==========================================
            # TABLE
            # ==========================================

            st.markdown("### Key Metrics")

            st.dataframe(
                format_large_numbers(
                    balance_display.T,
                    currency
                ),
                use_container_width=True
            )

        except Exception as e:

            st.warning(
                "Balance sheet unavailable"
            )

            st.code(str(e))

    # ------------------------------------------------
    # CASH FLOW STATEMENT
    # ------------------------------------------------

    with st.expander("Cash Flow Statement"):

        try:

            cashflow_metrics = [
                "Operating Cash Flow",
                "Free Cash Flow",
                "Capital Expenditure"
            ]

            cashflow_display = cashflow.loc[
                cashflow.index.intersection(
                    cashflow_metrics
                )
            ]

            # ==========================================
            # FREE CASH FLOW CHART
            # ==========================================

            if "Free Cash Flow" in cashflow.index:

                st.markdown(
                    "### Free Cash Flow Trend"
                )

                fcf = cashflow.loc[
                    "Free Cash Flow"
                ]

                fcf_df = (
                    fcf
                    .reset_index()
                )

                fcf_df.columns = [
                    "Date",
                    "FCF"
                ]

                fcf_df["FCF"] = (
                    fcf_df["FCF"]
                    / statement_divisor
                )

                fig = px.line(
                    fcf_df,
                    x="Date",
                    y="FCF",
                    markers=True
                )

                fig.update_layout(
                    template="plotly_dark",

                    height=400,

                    title="Free Cash Flow Trend",

                    title_x=0.02,

                    xaxis_title="Year",

                    yaxis_title=f"FCF ({statement_unit})"
                )

                fig.update_traces(
                    line=dict(width=3)
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    key="fcf_chart"
                )

            # ==========================================
            # TABLE
            # ==========================================

            st.markdown("### Key Metrics")

            st.dataframe(
                format_large_numbers(
                    cashflow_display.T,
                    currency
                ),
                use_container_width=True
            )

        except Exception as e:

            st.warning(
                "Cash flow statement unavailable"
            )

            st.code(str(e))            
# ===================================================
# DCF TAB
# ===================================================

with tab3:

    st.subheader("💰 Automated DCF Valuation")

    try:

        # ------------------------------
        # FCF
        # ------------------------------

        try:
            fcf = cashflow.loc[
                "Free Cash Flow"
            ].iloc[0]

        except:

            operating_cf = cashflow.loc[
                "Operating Cash Flow"
            ].iloc[0]

            capex = cashflow.loc[
                "Capital Expenditure"
            ].iloc[0]

            fcf = operating_cf + capex

        # ------------------------------
        # GROWTH RATE
        # ------------------------------

        revenues = financials.loc[
            "Total Revenue"
        ]

        growth_rates = (
            revenues.pct_change().dropna()
        )

        avg_growth = growth_rates.mean()

        avg_growth = min(
            max(avg_growth, 0.03),
            0.20
        )

        # ------------------------------
        # USER INPUTS
        # ------------------------------

        growth_rate = st.slider(
            "Growth Rate",
            0.01,
            0.25,
            float(avg_growth),
            0.01
        )

        discount_rate = st.slider(
            "Discount Rate",
            0.05,
            0.20,
            0.12,
            0.01
        )

        terminal_growth = st.slider(
            "Terminal Growth",
            0.01,
            0.06,
            0.04,
            0.01
        )

        # ------------------------------
        # FORECAST
        # ------------------------------

        forecast_years = 5

        future_fcfs = []

        current_fcf = fcf

        for i in range(forecast_years):

            current_fcf *= (
                1 + growth_rate
            )

            future_fcfs.append(current_fcf)

        # ------------------------------
        # DISCOUNT
        # ------------------------------

        present_values = []

        for i, future_fcf in enumerate(
            future_fcfs,
            start=1
        ):

            pv = (
                future_fcf
                / (
                    (1 + discount_rate)
                    ** i
                )
            )

            present_values.append(pv)

        # ------------------------------
        # TERMINAL VALUE
        # ------------------------------

        terminal_value = (
            future_fcfs[-1]
            * (1 + terminal_growth)
        ) / (
            discount_rate
            - terminal_growth
        )

        terminal_pv = (
            terminal_value
            / (
                (1 + discount_rate)
                ** forecast_years
            )
        )

        enterprise_value = (
            sum(present_values)
            + terminal_pv
        )

        # ------------------------------
        # BALANCE SHEET
        # ------------------------------

        try:
            cash = balance_sheet.loc[
                "Cash And Cash Equivalents"
            ].iloc[0]
        except:
            cash = 0

        try:
            debt = balance_sheet.loc[
                "Total Debt"
            ].iloc[0]
        except:
            debt = 0

        equity_value = (
            enterprise_value
            + cash
            - debt
        )

        shares_outstanding = info.get(
            "sharesOutstanding",
            1
        )

        intrinsic_value = (
            equity_value
            / shares_outstanding
        )

        upside = (
            (
                intrinsic_value
                - current_price
            )
            / current_price
        ) * 100

        # ------------------------------
        # DISPLAY
        # ------------------------------

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Intrinsic Value",
            format_money(intrinsic_value, currency, compact=False)
        )

        col2.metric(
            "Current Price",
            format_money(current_price, currency, compact=False)
        )

        col3.metric(
            "Upside / Downside",
            f"{upside:.2f}%"
        )

        # ------------------------------
        # ASSUMPTIONS
        # ------------------------------

        with st.expander(
            "DCF Assumptions"
        ):

            st.write(
                f"Free Cash Flow: {format_money(fcf, currency)}"
            )

            st.write(
                f"Growth Rate: {growth_rate:.2%}"
            )

            st.write(
                f"Discount Rate: {discount_rate:.2%}"
            )

            st.write(
                f"Terminal Growth: {terminal_growth:.2%}"
            )

    except Exception as e:

        st.error(
            "DCF valuation unavailable"
        )

        st.code(str(e))

# ===================================================
# NEWS TAB
# ===================================================

with tab4:

    st.subheader("📰 Latest News")

    if news:

        for article in news[:5]:

            with st.container(border=True):

                st.subheader(
                    article.get(
                        "title",
                        "No Title"
                    )
                )

                st.caption(
                    article.get(
                        "publisher",
                        "Unknown"
                    )
                )

                link = article.get(
                    "link",
                    "#"
                )

                st.link_button(
                    "Read Article",
                    link
                )

    else:

        st.info(
            "No news available."
        )
# ===================================================
# HISTORICAL PRICES TAB
# ===================================================

with tab5:

    st.subheader("📈 Historical Price Data")

    col1, col2, col3, col4 = st.columns(4)

    try:

        high_52 = hist["High"].max()

        low_52 = hist["Low"].min()

        avg_volume = int(hist["Volume"].mean())

        latest_close = hist["Close"].iloc[-1]

        col1.metric(
            "Latest Close",
            format_money(latest_close, currency, compact=False)
        )

        col2.metric(
            "Period High",
            format_money(high_52, currency, compact=False)
        )

        col3.metric(
            "Period Low",
            format_money(low_52, currency, compact=False)
        )

        col4.metric(
            "Avg Volume",
            f"{avg_volume:,}"
        )

    except:
        pass

    st.markdown("### Download Historical Prices")

    csv_df = hist.copy().reset_index()
    date_column = csv_df.columns[0]
    csv_df[date_column] = (
        pd.to_datetime(csv_df[date_column])
        .dt.strftime("%Y-%m-%d")
    )
    csv_df = csv_df.rename(columns={date_column: "Date"})

    csv = csv_df.to_csv(index=False).encode("utf-8-sig")

    st.download_button(
        label="⬇ Download CSV",
        data=csv,
        file_name=f"{ticker}_historical_prices.csv",
        mime="text/csv"
    )

    st.markdown("### Price Table")

    display_df = hist.copy()

    display_df.index = (
        display_df.index
        .strftime("%Y-%m-%d")
    )

    st.dataframe(
        display_df,
        use_container_width=True
    )

    st.markdown("### Returns Distribution")

    returns = (
        hist["Close"]
        .pct_change()
        .dropna()
    )

    fig = px.histogram(
        returns,
        nbins=40,
        title="Daily Return Distribution"
    )

    fig.update_layout(
        template="plotly_dark"
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        key="returns_distribution"
    )
    
# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.divider()

st.markdown("""
### 🚀 Features Included
- Live stock data
- Interactive candlestick charts
- Volume analysis
- Financial statements
- Automated DCF valuation
- Interactive DCF sliders
- News integration
- Multi-tab professional UI
""")
