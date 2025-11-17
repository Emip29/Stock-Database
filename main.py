import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

st.title("📈 Stock Dashboard")

ticker = st.sidebar.text_input("Ticker (ex: AAPL, TSLA, MSFT)")
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

if ticker:
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.error("⚠️ No price data found. Try another ticker.")
        st.stop()

    price_col = "Adj Close" if "Adj Close" in data.columns else "Close"

    # ---------------------------------------
    # FIXED PLOT (narwhals-safe)
    # ---------------------------------------
    df_plot = data.reset_index()

    fig = px.line(
        df_plot,
        x="Date",
        y=price_col,
        title=f"{ticker} Price Chart"
    )
    st.plotly_chart(fig)

    pricing_data, fundamental_data, news = st.tabs(
        ["📊 Pricing Data", "📚 Fundamental Data", "📰 Top News"]
    )

    # ---------------------------------------
    # PRICING DATA
    # ---------------------------------------
    with pricing_data:
        st.header("Price Movements")

        data2 = data.copy()
        data2["% Change"] = data2[price_col].pct_change()
        data2.dropna(inplace=True)

        st.write(data2)

        annual_return = data2["% Change"].mean() * 252 * 100
        stdev = np.std(data2["% Change"]) * np.sqrt(252) * 100

        st.write(f"**Annual Return:** {annual_return:.2f}%")
        st.write(f"**Standard Deviation:** {stdev:.2f}%")

        # Moving averages
        data2["MA20"] = data2[price_col].rolling(20).mean()
        data2["MA50"] = data2[price_col].rolling(50).mean()
        data2["MA200"] = data2[price_col].rolling(200).mean()

        st.line_chart(data2[[price_col, "MA20", "MA50", "MA200"]])

    # ---------------------------------------
    # FUNDAMENTALS
    # ---------------------------------------
    from alpha_vantage.fundamentaldata import FundamentalData
    with fundamental_data:
        key = "XCWQ3FD4VCKVL1NA"
        fd = FundamentalData(key, output_format="pandas")

        st.subheader("Balance Sheet")
        balance_sheet = fd.get_balance_sheet_annual(ticker)[0]
        bs = balance_sheet.T[2:]
        bs.columns = list(balance_sheet.T.iloc[0])
        st.write(bs)

        st.subheader("Income Statement")
        income_statement = fd.get_income_statement_annual(ticker)[0]
        is1 = income_statement.T[2:]
        is1.columns = list(income_statement.T.iloc[0])
        st.write(is1)

        st.subheader("Cash Flow Statement")
        cash_flow = fd.get_cash_flow_annual(ticker)[0]
        cf = cash_flow.T[2:]
        cf.columns = list(cash_flow.T.iloc[0])
        st.write(cf)

    # ---------------------------------------
    # NEWS TAB
    # ---------------------------------------
    from stocknews import StockNews

    with news:
        st.header(f"News for {ticker}")

        sn = StockNews(ticker, save_news=False)
        df_news = sn.read_rss()

        for i in range(10):
            st.subheader(f"News {i + 1}")
            st.write(df_news["published"][i])
            st.write(df_news["title"][i])
            st.write(df_news["summary"][i])

            st.write(f"Title Sentiment: {df_news['sentiment_title'][i]}")
            st.write(f"Summary Sentiment: {df_news['sentiment_summary'][i]}")
