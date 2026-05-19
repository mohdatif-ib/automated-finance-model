# charts.py

import plotly.graph_objects as go
from plotly.subplots import make_subplots


# ---------------------------------------------------
# MAIN CHART FUNCTION
# ---------------------------------------------------

def create_candlestick_chart(
    hist,
    show_volume=True,
    show_sma=True
):

    rows = 3 if show_volume else 2

    fig = make_subplots(
    rows=rows,
    cols=1,
    shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.6, 0.2, 0.2]
    if show_volume else [0.8, 0.2]
    )   
    

    # ------------------------------------------------
    # CANDLESTICK
    # ------------------------------------------------

    fig.add_trace(
        go.Candlestick(
            x=hist.index,
            open=hist["Open"],
            high=hist["High"],
            low=hist["Low"],
            close=hist["Close"],
            name="Price"
        ),
        row=1,
        col=1
    )

    # ------------------------------------------------
    # MOVING AVERAGES
    # ------------------------------------------------

    if show_sma:

        # SMA 50
        if "SMA_50" in hist.columns:

            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist["SMA_50"],
                    mode="lines",
                    name="SMA 50"
                ),
                row=1,
                col=1
            )

        # SMA 200
        if "SMA_200" in hist.columns:

            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist["SMA_200"],
                    mode="lines",
                    name="SMA 200"
                ),
                row=1,
                col=1
            )

# ------------------------------------------------
# RSI
# ------------------------------------------------

    if "RSI" in hist.columns:
    
        rsi_row = 3 if show_volume else 2
    
        fig.add_trace(
            go.Scatter(
                x=hist.index,
                y=hist["RSI"],
                mode="lines",
                name="RSI"
            ),
            row=rsi_row,
            col=1
        )
    
        # Overbought Line
    
        fig.add_hline(
            y=70,
            line_dash="dash",
            row=rsi_row,
            col=1
        )
    
        # Oversold Line
    
        fig.add_hline(
            y=30,
            line_dash="dash",
            row=rsi_row,
            col=1
        )
    # ------------------------------------------------
    # VOLUME
    # ------------------------------------------------

    if show_volume:

        fig.add_trace(
            go.Bar(
                x=hist.index,
                y=hist["Volume"],
                name="Volume"
            ),
            row=2,
            col=1
        )

    # ------------------------------------------------
    # LAYOUT
    # ------------------------------------------------

    fig.update_layout(
        height=700,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(
            l=20,
            r=20,
            t=40,
            b=20
        )
    )

    fig.update_yaxes(
        title_text="Price",
        row=1,
        col=1
    )

    if show_volume:

        fig.update_yaxes(
            title_text="Volume",
            row=2,
            col=1
        )

    return fig

    if show_volume:
    
        fig.update_yaxes(
            title_text="RSI",
            row=3,
            col=1
        )
    
    else:   
    
        fig.update_yaxes(
            title_text="RSI",
            row=2,
            col=1
        )