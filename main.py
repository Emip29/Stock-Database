import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go

from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews

# ---------------------------------------------------------
# PAGE TITLE
# ---------------------------------------------------------
st.title("Stock Dashboard")

# ---------------------------------------------------------
# SIDEBAR INPUTS
# ---------------------------------------------------------
ticker = st.sidebar.text_input("Ticker")
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

# ---------------------------------------------------------
# DATA DOWNLOAD
# ---------------------------------------------------------
if ticker:
    data = yf.download(ticker, start=start_date, end=end_date)

    # Fix for missing Adj Close
    if "Adj Close" in data.columns:
        price_col = "Adj Close"
    else:
        price_col = "Close"

    # ---------------------------------------------------------
    # MAIN PRICE CHART (graph_objects)
    # ---------------------------------------------------------
    df_plot = data.reset_index()
    df_plot["Date"] = pd.to_datetime(df_plot["Date"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_plot["Date"],
        y=df_plot[price_col],
        mode="lines",
        name=price_col
    ))

    fig.update_layout(
        title=f"{ticker} Price Chart",
        xaxis_title="Date",
        yaxis_title=price_col
    )

    st.plotly_chart(fig)

    # ---------------------------------------------------------
    # TABS
    # ---------------------------------------------------------
    pricing_data, fundamental_data, news_tab = st.tabs(
        ["Pricing Data", "Fundamental Data", "Top 10 News"]
    )

    # =========================================================
    # PRICING DATA TAB
    # =========================================================
    with pricing_data:
        st.header("Price Movements")

        data2 = data.copy()

        # Fix percentage change bug
        data2["% Change"] = data2[price_col].pct_change()

        data2.dropna(inplace=True)
        st.write(data2)

        # Annual return + standard deviation
        annual_return = data2["% Change"].mean() * 252 * 100
        st.write("Annual Return:", round(annual_return, 2), "%")

        stdev = np.std(data2["% Change"]) * np.sqrt(252) * 100
        st.write("Standard Deviation:", round(stdev, 2), "%")

    # =========================================================
    # FUNDAMENTAL DATA TAB
    # =========================================================
    with fundamental_data:
        st.header("Fundamental Data")

        key = "XCWQ3FD4VCKVL1NA"
        fd = FundamentalData(key, output_format="pandas")

        # ---------------------
        # BALANCE SHEET
        # ---------------------
        st.subheader("Balance Sheet")
        balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
        bs = balance_sheet.T[2:]
        bs.columns = list(balance_sheet.T.iloc[0])
        st.write(bs)

        # ---------------------
        # INCOME STATEMENT
        # ---------------------
        st.subheader("Income Statement")
        income_statement = fd.get_income_statement_annual(ticker)[0]
        is1 = income_statement.T[2:]
        is1.columns = list(income_statement.T.iloc[0])
        st.write(is1)

        # ---------------------
        # CASH FLOW STATEMENT
        # ---------------------
        st.subheader("Cash Flow Statement")
        cash_flow = fd.get_cash_flow_annual(ticker)[0]
        cf = cash_flow.T[2:]
        cf.columns = list(cash_flow.T.iloc[0])
        st.write(cf)

    # =========================================================
    # NEWS TAB
    # =========================================================
    with news_tab:
        st.header(f"Top 10 News for {ticker}")

        try:
            sn = StockNews(ticker, save_news=False)
            df_news = sn.read_rss()

            for i in range(10):
                st.subheader(f"News {i+1}")

                st.write("Published:", df_news["published"][i])
                st.write("Title:", df_news["title"][i])
                st.write("Summary:", df_news["summary"][i])

                st.write("Title Sentiment:", df_news["sentiment_title"][i])
                st.write("News Sentiment:", df_news["sentiment_summary"][i])
                st.markdown("---")

        except Exception as e:
            st.error("News could not be loaded. RSS feed may be rate-limited.")
            st.write(e)
