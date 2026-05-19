# financials.py

import streamlit as st


def display_income_statement(financials):

    important_metrics = [
        "Total Revenue",
        "Gross Profit",
        "Operating Income",
        "EBITDA",
        "Net Income"
    ]

    filtered = financials.loc[
        financials.index.intersection(
            important_metrics
        )
    ]

    st.dataframe(
        filtered.T,
        use_container_width=True
    )