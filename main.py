import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px

# --------------------------------------------
# TITLE + SIDEBAR
# --------------------------------------------
st.title("📈 Stock Dashboard")

ticker = st.sidebar.text_input("Ticker (ex: AAPL, TSLA, MSFT)")
start_date = st.sidebar.date_input("Start Date")
end_date = st.sidebar.date_input("End Date")

# --------------------------------------------
# DOWNLOAD DATA
# --------------------------------------------
if ticker:
    data = yf.download(ticker, start=start_date, end=end_date)

    if data.empty:
        st.error("⚠️ No data found for this ticker.")
        st.stop()

    # Use Adj Close if exists, else Close
    price_col = "Adj Close" if "Adj Close" in data.columns else "Close"

    # --------------------------------------------
    # PRICE CHART
    # --------------------------------------------
    fig = px.line(
        data,
        x=data.index,
        y=data[price_col],
        title=f"{ticker} Price Chart",
        labels={"x": "Date", "y": price_col}
    )
    st.plotly_chart(fig)

    # --------------------------------------------
    # TABS
    # --------------------------------------------
    pricing_data, fundamental_data, news = st.tabs(
        ["📊 Pricing Data", "📚 Fundamental Data", "📰 Top 10 News"]
    )

    # --------------------------------------------
    # PRICING DATA TAB
    # --------------------------------------------
    with pricing_data:
        st.header("Price Movements")

        data2 = data.copy()
        data2["% Change"] = data2[price_col].pct_change()
        data2.dropna(inplace=True)

        st.write(data2)

        # Stats
        annual_return = data2["% Change"].mean() * 252 * 100
        stdev = np.std(data2["% Change"]) * np.sqrt(252) * 100

        st.write(f"**Annual Return:** {annual_return:.2f}%")
        st.write(f"**Standard Deviation:** {stdev:.2f}%")

        # -------------------------
        # TECHNICAL INDICATORS
        # -------------------------
        st.subheader("Technical Indicators")

        # Moving Averages
        data2["MA20"] = data2[price_col].rolling(20).mean()
        data2["MA50"] = data2[price_col].rolling(50).mean()
        data2["MA200"] = data2[price_col].rolling(200).mean()

        # RSI
        delta = data2[price_col].diff()
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = pd.Series(gain).rolling(window=14).mean()
        avg_loss = pd.Series(loss).rolling(window=14).mean()

        rs = avg_gain / avg_loss
        data2["RSI"] = 100 - (100 / (1 + rs))

        # MACD
        exp1 = data2[price_col].ewm(span=12, adjust=False).mean()
        exp2 = data2[price_col].ewm(span=26, adjust=False).mean()
        data2["MACD"] = exp1 - exp2
        data2["Signal"] = data2["MACD"].ewm(span=9, adjust=False).mean()

        st.line_chart(data2[[price_col, "MA20", "MA50", "MA200"]])
        st.line_chart(data2["RSI"])
        st.line_chart(data2[["MACD", "Signal"]])

    # --------------------------------------------
    # FUNDAMENTALS TAB
    # --------------------------------------------
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

    # --------------------------------------------
    # NEWS TAB
    # --------------------------------------------
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

            title_sentiment = df_news["sentiment_title"][i]
            summary_sentiment = df_news["sentiment_summary"][i]

            st.write(f"Title Sentiment Score: **{title_sentiment}**")
            st.write(f"News Sentiment Score: **{summary_sentiment}**")
