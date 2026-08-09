import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands
from datetime import datetime

st.set_page_config(page_title="RB PSX Pro Auto", layout="wide", page_icon="📈")
st.title("📈 RB PSX Pro - Full Auto Scanner")
st.markdown("**Auto Data from PSX | FFC | EFERT | NBP | LUCK | MZNPETF | FABL**")

TICKERS = ["FFC", "EFERT", "NBP", "LUCK", "MZNPETF", "FABL"]
TELEGRAM_TOKEN = st.secrets.get("TELEGRAM_TOKEN", "") 
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "")

def send_telegram(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        except: pass

@st.cache_data(ttl=1800)
def fetch_psx_data():
    all_data = []
    base_url = "https://dps.psx.com.pk"
    for ticker in TICKERS:
        try:
            url = f"{base_url}/historical-data/{ticker}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                data = r.json()
                df = pd.DataFrame(data['data'])
                df['Ticker'] = ticker
                df = df.rename(columns={'date':'Date','open':'Open','high':'High','low':'Low','close':'Close','volume':'Volume'})
                all_data.append(df)
        except: pass
    if all_data:
        final_df = pd.concat(all_data)
        final_df['Date'] = pd.to_datetime(final_df['Date'])
        return final_df
    return pd.DataFrame()

df = fetch_psx_data()

if not df.empty:
    st.success(f"Data Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    results = []
    for ticker in TICKERS:
        data = df[df['Ticker'] == ticker].copy().sort_values('Date').tail(250)
        if len(data) < 50: continue
        data['SMA50'] = SMAIndicator(data['Close'], 50).sma_indicator()
        data['SMA200'] = SMAIndicator(data['Close'], 200).sma_indicator()
        data['RSI'] = RSIIndicator(data['Close']).rsi()
        macd = MACD(data['Close'])
        data['MACD'] = macd.macd()
        data['MACD_signal'] = macd.macd_signal()
        bb = BollingerBands(data['Close'])
        data['BB_low'] = bb.bollinger_lband()
        data['BB_high'] = bb.bollinger_hband()
        latest = data.iloc[-1]
        score = 0
        if latest['SMA50'] > latest['SMA200']: score += 1
        if latest['RSI'] < 40: score += 1
        if latest['MACD'] > latest['MACD_signal']: score += 1
        if latest['Close'] < latest['BB_low']: score += 1
        if score >= 3: signal = "🚨 STRONG BUY"
        elif score >= 1: signal = "BUY"
        elif score <= -3: signal = "🚨 STRONG SELL"
        elif score <= -1: signal = "SELL"
        else: signal = "HOLD"
        results.append({"Ticker": ticker, "Price": f"Rs.{latest['Close']:.2f}", "Signal": signal, "RSI": f"{latest['RSI']:.1f}"})
    
    selected = st.selectbox("Stock Select Karein", TICKERS)
    plot_data = df[df['Ticker'] == selected].tail(120)
    fig = go.Figure()
    fig.add_trace(go.Candlestick(x=plot_data['Date'], open=plot_data['Open'], high=plot_data['High'], low=plot_data['Low'], close=plot_data['Close']))
    fig.add_trace(go.Scatter(x=plot_data['Date'], y=plot_data['SMA50'], name='SMA50'))
    fig.add_trace(go.Scatter(x=plot_data['Date'], y=plot_data['SMA200'], name='SMA200'))
    st.plotly_chart(fig, use_container_width=True)
    st.subheader("🔍 Live Scan - All 6 Stocks")
    st.dataframe(pd.DataFrame(results), use_container_width=True)
else:
    st.error("PSX se data fetch nahi hua. 5 min baad try karein.")
