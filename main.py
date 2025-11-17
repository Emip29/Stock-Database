import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from alpha_vantage.fundamentaldata import FundamentalData
from stocknews import StockNews

st.title("Stock Dashboard")

# ---------------- Sidebar Inputs ----------------
ticker = st.sidebar.text_input("Ticker (e.g. AAPL)").upper()
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

# ---------------- Validation ----------------
if not ticker:
    st.warning("Please enter a ticker symbol.")
    st.stop()

if start_date >= end_date:
    st.error("Start date must be before end date.")
    st.stop()

# ---------------- Download Stock Data ----------------
data = yf.download(ticker, start=start_date, end=end_date)

if data.empty:
    st.error("No stock data found. Check ticker or date range.")
    st.stop()

# Fix MultiIndex columns
if isinstance(data.columns, pd.MultiIndex):
    data.columns = data.columns.get_level_values(0)

# Normalize "Adj Close"
if "Adj Close" not in data.columns:
    # Sometimes yfinance uses AdjClose
    if "AdjClose" in data.columns:
        data.rename(columns={"AdjClose": "Adj Close"}, inplace=True)
    else:
        st.error("'Adj Close' column not found in downloaded data.")
        st.write("Columns returned:", list(data.columns))
        st.stop()

# ---------------- Price Chart ----------------
fig = px.line(data, x=data.index, y=data["Adj Close"], title=f"{ticker} Adjusted Closing Prices")
st.plotly_chart(fig)

# ---------------- Tabs ----------------
pricing_data, fundamental_data, news = st.tabs(
    ["Pricing Data", "Fundamental Data", "Top 10 News"]
)

# ---------------- PRICING DATA TAB ----------------
with pricing_data:
    st.header("Price Movements")

    data2 = data.copy()
    data2["% Change"] = data2["Adj Close"].pct_change()
    data2.dropna(inplace=True)

    st.write(data2)

    annual_return = data2["% Change"].mean() * 252 * 100
    st.write("Annual Return:", round(annual_return, 2), "%")

    stdev = np.std(data2["% Change"]) * np.sqrt(252)
    st.write("Standard Deviation:", round(stdev * 100, 2), "%")

# ---------------- FUNDAMENTAL DATA TAB ----------------
with fundamental_data:
    st.header("Fundamental Data")

    key = "XCWQ3FD4VCKVL1NA"  # Your Alpha Vantage key
    fd = FundamentalData(key, output_format="pandas")

    # BALANCE SHEET
    st.subheader("Balance Sheet")
    balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
    bs = balance_sheet.T[2:]
    bs.columns = list(balance_sheet.T.iloc[0])
    st.write(bs)

    # INCOME STATEMENT
    st.subheader("Income Statement")
    income_statement = fd.get_income_statement_annual(ticker)[0]
    is1 = income_statement.T[2:]
    is1.columns = list(income_statement.T.iloc[0])
    st.write(is1)

    # CASH FLOW
    st.subheader("Cash Flow Statement")
    cash_flow = fd.get_cash_flow_annual(ticker)[0]
    cf = cash_flow.T[2:]
    cf.columns = list(cash_flow.T.iloc[0])
    st.write(cf)

with news:
    st.header(f"News for {ticker}")

    try:
        sn = StockNews(ticker, save_news=False)
        df_news = sn.read_rss()

        for i in range(min(10, len(df_news))):
            st.subheader(f"News {i+1}")
            st.write(df_news["published"][i])
            st.write(df_news["title"][i])
            st.write(df_news["summary"][i])

            title_sentiment = df_news["sentiment_title"][i]
            news_sentiment = df_news["sentiment_summary"][i]

            st.write(f"Title Sentiment: {title_sentiment}")
            st.write(f"News Sentiment: {news_sentiment}")

    except Exception as e:
        st.error("Could not load news.")
        st.write(e)
