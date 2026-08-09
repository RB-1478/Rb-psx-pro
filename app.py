import streamlit as st
import pandas as pd
import yfinance as yf
from ta.momentum import RSIIndicator

st.set_page_config(page_title="RB PSX Pro", layout="wide")
st.title("📈 RB PSX Pro - Full Auto Scanner")
st.markdown("**Auto Data from PSX | FFC, EFERT, NBP, LUCK, OGDC, PPL, HBL**")

TICKERS = ["FFC.KAR", "EFERT.KAR", "NBP.KAR", "LUCK.KAR", "OGDC.KAR", "PPL.KAR", "HBL.KAR"]

def fetch_data(ticker):
    try:
        data = yf.download(ticker, period="6mo", interval="1d", progress=False)
        if data.empty:
            st.error(f"{ticker} ka data nahi mila")
            return None
        data['RSI'] = RSIIndicator(data['Close']).rsi()
        return data
    except:
        st.error(f"{ticker} fetch karne me error")
        return None

for ticker in TICKERS:
    st.subheader(ticker.replace(".KAR",""))
    df = fetch_data(ticker)
    if df is not None:
        st.write(f"Last Price: {df['Close'][-1]:.2f}")
        st.write(f"RSI: {df['RSI'][-1]:.2f}")
        st.line_chart(df['Close'])
