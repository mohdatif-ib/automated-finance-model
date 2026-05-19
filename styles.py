# styles.py

import streamlit as st


def load_css():

    st.markdown("""
    <style>

    /* -------------------------------------------------
       MAIN APP
    ------------------------------------------------- */

    .main {
        background-color: #0E1117;
        color: #FAFAFA;
    }

    section[data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #222;
    }

    /* -------------------------------------------------
       METRIC CARDS
    ------------------------------------------------- */

    div[data-testid="metric-container"] {

        background: linear-gradient(
            145deg,
            #1f1f1f,
            #151515
        );

        border: 1px solid #2d2d2d;

        padding: 18px;

        border-radius: 16px;

        box-shadow:
            0 4px 12px rgba(0,0,0,0.35);

        transition: 0.3s;
    }

    div[data-testid="metric-container"]:hover {

        transform: translateY(-2px);

        border: 1px solid #3b82f6;
    }

    /* -------------------------------------------------
       TABS
    ------------------------------------------------- */

    button[data-baseweb="tab"] {

        font-size: 16px;

        font-weight: 600;

        padding: 10px 18px;

        border-radius: 12px;

        margin-right: 8px;

        background-color: #161b22;

        color: white;
    }

    button[data-baseweb="tab"]:hover {

        background-color: #1f2937;
    }

    button[aria-selected="true"] {

        background-color: #2563eb !important;

        color: white !important;
    }

    /* -------------------------------------------------
       DATAFRAMES
    ------------------------------------------------- */

    .stDataFrame {

        border: 1px solid #2d2d2d;

        border-radius: 12px;

        overflow: hidden;
    }

    /* -------------------------------------------------
       EXPANDERS
    ------------------------------------------------- */

    details {

        background-color: #161b22;

        border: 1px solid #2d2d2d;

        border-radius: 12px;

        padding: 8px;

        margin-bottom: 12px;
    }

    /* -------------------------------------------------
       BUTTONS
    ------------------------------------------------- */

    .stButton>button {

        background-color: #2563eb;

        color: white;

        border-radius: 10px;

        border: none;

        padding: 10px 18px;

        font-weight: 600;

        transition: 0.3s;
    }

    .stButton>button:hover {

        background-color: #1d4ed8;

        transform: scale(1.02);
    }

    /* -------------------------------------------------
       DOWNLOAD BUTTON
    ------------------------------------------------- */

    .stDownloadButton>button {

        background-color: #059669;

        color: white;

        border-radius: 10px;

        border: none;

        padding: 10px 18px;

        font-weight: 600;
    }

    /* -------------------------------------------------
       INPUTS
    ------------------------------------------------- */

    .stSelectbox div[data-baseweb="select"] {

        background-color: #161b22;

        border-radius: 10px;
    }

    .stSlider {

        padding-top: 10px;
    }

    /* -------------------------------------------------
       HEADINGS
    ------------------------------------------------- */

    h1, h2, h3 {

        font-weight: 700;

        letter-spacing: 0.3px;
    }

    /* -------------------------------------------------
       SCROLLBAR
    ------------------------------------------------- */

    ::-webkit-scrollbar {
        width: 10px;
    }

    ::-webkit-scrollbar-track {
        background: #111827;
    }

    ::-webkit-scrollbar-thumb {
        background: #374151;
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: #4b5563;
    }

    </style>
    """, unsafe_allow_html=True)