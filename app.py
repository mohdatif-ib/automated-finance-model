# app.py
# RUN:
# streamlit run app.py

import streamlit as st
import yfinance as yf
from modules.charts import create_candlestick_chart
from modules.indicators import add_indicators
from utils import format_large_numbers
from styles import load_css
import plotly.express as px

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

company_dict = {
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

period = st.sidebar.selectbox(
    "Select Time Period",
    ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=3
)

show_volume = st.sidebar.checkbox(
    "Show Volume",
    value=True
)

# ---------------------------------------------------
# FETCH DATA
# ---------------------------------------------------

stock = yf.Ticker(ticker)

hist = stock.history(period=period)

info = stock.info

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

tab1, tab2, tab3, tab4 = st.tabs([
    "Overview",
    "Financials",
    "DCF Valuation",
    "News"
])

# ===================================================
# OVERVIEW TAB
# ===================================================

with tab1:

    st.subheader(f"{company} ({ticker})")

    # ------------------------------
    # METRICS
    # ------------------------------

    current_price = info.get("currentPrice", 0)

    market_cap = info.get("marketCap", 0)

    pe_ratio = info.get("trailingPE", "N/A")

    dividend_yield = info.get("dividendYield", 0)

    beta = info.get("beta", "N/A")

    if market_cap:
        market_cap = f"{market_cap / 1e12:.2f} T"

    if dividend_yield:
        dividend_yield = f"{dividend_yield * 100:.2f}%"

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "Current Price",
        f"₹{current_price:.2f}"
    )

    col2.metric(
        "Market Cap",
        market_cap
    )

    col3.metric(
        "P/E Ratio",
        pe_ratio
    )

    col4.metric(
        "Dividend Yield",
        dividend_yield
    )

    col5.metric(
        "Beta",
        beta
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

                # Convert to Crores

                revenue_df["Revenue"] = (
                    revenue_df["Revenue"]
                    / 1e7
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

                    yaxis_title="Revenue (₹ Cr)",

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
                    / 1e7
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

                    yaxis_title="Net Income (₹ Cr)",

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
                    income_display.T
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
                    / 1e7
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

                    yaxis_title="Assets (₹ Cr)"
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
                    balance_display.T
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
                    / 1e7
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

                    yaxis_title="FCF (₹ Cr)"
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
                    cashflow_display.T
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
            f"₹{intrinsic_value:.2f}"
        )

        col2.metric(
            "Current Price",
            f"₹{current_price:.2f}"
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
                f"Free Cash Flow: {fcf:,.0f}"
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