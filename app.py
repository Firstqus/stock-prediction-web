import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="AI Stock Advisor", layout="wide")

# ---------------------------------------------------------
# SESSION STATE DECLARATION
# ---------------------------------------------------------
if "lang" not in st.session_state:
    st.session_state.lang = "TH"

if "theme" not in st.session_state:
    st.session_state.theme = "Light"

if "show_tutorial" not in st.session_state:
    st.session_state.show_tutorial = True


# ---------------------------------------------------------
# LANGUAGE PACK
# ---------------------------------------------------------

TXT = {
    "TH": {
        "title": "📈 AI Stock Advisor – ระบบช่วยตัดสินใจซื้อขายหุ้น",
        "desc": """
ระบบวิเคราะห์แนวโน้มตลาดโดยอิงจากอินดิเคเตอร์มาตรฐาน เช่น  
**SMA, RSI, MACD** เพื่อช่วยให้คุณตัดสินใจ **ซื้อ / ถือ / ขาย** ได้อย่างมีเหตุผล
        """,
        "tutorial_title": "📘 วิธีใช้งานเบื้องต้น",
        "ticker_input": "พิมพ์ชื่อหุ้น",
        "category": "เลือกหมวดหมู่",
        "popular": "หุ้นยอดนิยม",
        "apply": "ใช้ตัวเลือกนี้",
        "period": "ช่วงเวลา",
        "analysis": "🔍 ผลการวิเคราะห์ AI",
        "score": "คะแนนแนวโน้ม",
        "reason_list": "📌 เหตุผลที่ AI ใช้พิจารณา",
        "chart": "📈 กราฟราคา + แนวโน้ม",
        "chart_desc": """
- **Candlestick** = ราคา  
- **SMA20** = แนวโน้มสั้น  
- **SMA50** = แนวโน้มกลาง  
ถ้า SMA20 ตัดขึ้น SMA50 = สัญญาณขาขึ้น
        """,
        "rsi": "RSI",
        "macd": "MACD",
        "rsi_desc": "RSI > 70 = Overbought | RSI < 30 = Oversold",
        "macd_desc": "MACD ตัดขึ้น Signal = ขาขึ้น | ตัดลง = ขาลง",
        "buy": "🟢 แนะนำ: ซื้อ (Strong Buy)",
        "hold": "🟡 แนะนำ: ถือ (Hold)",
        "sell": "🔴 แนะนำ: ขาย (Sell)",
        "invalid": "❌ ไม่พบข้อมูลหุ้น กรุณาตรวจสอบชื่อให้ถูกต้อง",
    },

    "EN": {
        "title": "📈 AI Stock Advisor – Buy/Sell Decision System",
        "desc": """
This system analyzes market trends using technical indicators  
such as **SMA, RSI, MACD** to help you decide when to **Buy / Hold / Sell**.
        """,
        "tutorial_title": "📘 Quick Start Guide",
        "ticker_input": "Enter stock ticker",
        "category": "Select Category",
        "popular": "Popular Stocks",
        "apply": "Apply",
        "period": "Time Range",
        "analysis": "🔍 AI Analysis Result",
        "score": "Trend Score",
        "reason_list": "📌 AI Analysis Reason",
        "chart": "📈 Price Chart + Trend",
        "chart_desc": """
- **Candlestick** = Price  
- **SMA20** = Short-term trend  
- **SMA50** = Mid-term trend  
If SMA20 crosses above SMA50 = Bullish signal
        """,
        "rsi": "RSI",
        "macd": "MACD",
        "rsi_desc": "RSI > 70 = Overbought | RSI < 30 = Oversold",
        "macd_desc": "MACD above Signal = Bullish | Below = Bearish",
        "buy": "🟢 Strong Buy",
        "hold": "🟡 Hold",
        "sell": "🔴 Sell",
        "invalid": "❌ No data found. Please check the ticker symbol.",
    }
}

LANG = TXT[st.session_state.lang]

# ---------------------------------------------------------
# TOP MENU: LANGUAGE + THEME
# ---------------------------------------------------------

col_menu1, col_menu2, col_menu3 = st.columns([2,1,1])

with col_menu2:
    lang = st.selectbox("🌐 Language", ["TH", "EN"], index=0 if st.session_state.lang=="TH" else 1)
    st.session_state.lang = lang
    LANG = TXT[lang]

with col_menu3:
    theme = st.selectbox("🎨 Theme", ["Dark",], index=0)
    st.session_state.theme = theme


# ---------------------------------------------------------
# APPLY THEME
# ---------------------------------------------------------

if theme == "Dark":
    st.markdown("""
        <style>
        body { background-color: #0f1116; color: white; }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# TUTORIAL (SHOW ONLY ON FIRST LOAD)
# ---------------------------------------------------------
if st.session_state.show_tutorial:
    st.header(LANG["tutorial_title"])
    st.info("""
- เลือกหุ้น หรือ พิมพ์ Ticker เช่น AAPL, TSLA  
- ระบบจะโหลดข้อมูลย้อนหลังตามช่วงเวลาที่เลือก  
- AI จะวิเคราะห์จาก SMA, RSI, MACD  
- คะแนนสูง → Buy, คะแนนต่ำ → Sell  
""")
    st.button("เริ่มใช้งาน", on_click=lambda: st.session_state.update({"show_tutorial": False}))
    st.stop()


# ---------------------------------------------------------
# MAIN TITLE
# ---------------------------------------------------------
st.title(LANG["title"])
st.write(LANG["desc"])


# ---------------------------------------------------------
# STOCK SELECTION
# ---------------------------------------------------------

popular_stocks = {
    "US": ["AAPL", "MSFT", "AMZN", "NVDA", "META", "TSLA", "GOOGL"],
    "TH": ["PTT.BK", "AOT.BK", "SCB.BK", "KBANK.BK", "CPALL.BK"],
    "Crypto": ["BTC-USD", "ETH-USD", "BNB-USD"]
}

st.subheader("🔍 Stock Selection")

colA, colB = st.columns([2,1])

with colA:
    ticker = st.text_input(LANG["ticker_input"], "AAPL")

with colB:
    cat = st.selectbox(LANG["category"], list(popular_stocks.keys()))
    pick = st.selectbox(LANG["popular"], popular_stocks[cat])
    if st.button(LANG["apply"]):
        ticker = pick

period = st.selectbox(LANG["period"], ["3mo","6mo","1y","2y","5y"], index=2)


# ---------------------------------------------------------
# LOAD STOCK DATA
# ---------------------------------------------------------

@st.cache_data
def load_stock(symbol, period):
    df = yf.download(symbol, period=period, auto_adjust=True)
    df.reset_index(inplace=True)
    return df

df = load_stock(ticker, period)

if df.empty:
    st.error(LANG["invalid"])
    st.stop()

df.columns = df.columns.get_level_values(0)
df = df.loc[:, ~df.columns.duplicated()]

# ---------------------------------------------------------
# CALCULATE INDICATORS
# ---------------------------------------------------------
df["SMA20"] = df["Close"].rolling(20).mean()
df["SMA50"] = df["Close"].rolling(50).mean()

delta = df["Close"].diff()
gain = delta.where(delta > 0, 0)
loss = -delta.where(delta < 0, 0)
rs = gain.rolling(14).mean() / loss.rolling(14).mean()
df["RSI"] = 100 - (100 / (1 + rs))

df["EMA12"] = df["Close"].ewm(span=12).mean()
df["EMA26"] = df["Close"].ewm(span=26).mean()
df["MACD"] = df["EMA12"] - df["EMA26"]
df["Signal"] = df["MACD"].ewm(span=9).mean()

df = df.dropna()


# ---------------------------------------------------------
# DECISION ENGINE
# ---------------------------------------------------------
def decide(df):
    # เลือกเฉพาะ column ที่เป็น numeric
    numeric_cols = df.select_dtypes(include=[np.number]).columns

    # ดึงแถวสุดท้ายเฉพาะตัวเลข
    L = df[numeric_cols].iloc[-1]

    score = 50
    reasons = []

    # ----- SMA Trend -----
    if float(L["SMA20"]) > float(L["SMA50"]):
        score += 15
        reasons.append("📈 SMA20 > SMA50: แนวโน้มขาขึ้น")
    else:
        score -= 15
        reasons.append("📉 SMA20 < SMA50: แนวโน้มอ่อนแรง")

    # ----- RSI -----
    if float(L["RSI"]) < 30:
        score += 20
        reasons.append("🟢 RSI < 30 → Oversold")
    elif float(L["RSI"]) > 70:
        score -= 20
        reasons.append("🔴 RSI > 70 → Overbought")

    # ----- MACD -----
    if float(L["MACD"]) > float(L["Signal"]):
        score += 15
        reasons.append("📈 MACD ตัดขึ้น Signal → โมเมนตัมบวก")
    else:
        score -= 15
        reasons.append("📉 MACD ตัดลง Signal → โมเมนตัมลบ")

    # ----- Price vs SMA50 -----
    if float(L["Close"]) > float(L["SMA50"]):
        score += 10
        reasons.append("💵 ราคายืนเหนือ SMA50 → Buyers คุมตลาด")
    else:
        score -= 10
        reasons.append("⚠️ ราคาต่ำกว่า SMA50 → เสี่ยงลง")

    # Normalize 0–100
    score = max(0, min(100, score))

    # Final Decision
    if score >= 70:
        decision = "🟢 แนะนำ: ซื้อ (Strong Buy)"
    elif score >= 55:
        decision = "🟡 แนะนำ: ถือ (Hold)"
    else:
        decision = "🔴 แนะนำ: ขาย (Sell)"

    return score, decision, reasons
try:
    score, decision, reasons = decide(df)
except Exception as e:
    st.error(f"เกิดข้อผิดพลาดในระบบตัดสินใจ: {e}")
    st.stop()

# ---------------------------------------------------------
# DISPLAY DECISION
# ---------------------------------------------------------
st.subheader(LANG["analysis"])
st.metric(LANG["score"], f"{score}/100")

if "Buy" in decision or "ซื้อ" in decision:
    st.success(decision)
elif "Sell" in decision or "ขาย" in decision:
    st.error(decision)
else:
    st.warning(decision)

with st.expander(LANG["reason_list"]):
    for r in reasons:
        st.write("• " + r)


# ---------------------------------------------------------
# PRICE CHART
# ---------------------------------------------------------
st.subheader(LANG["chart"])

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["Date"], open=df["Open"],
    high=df["High"], low=df["Low"], close=df["Close"],
    name="Price"
))

fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20"))
fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA50"], name="SMA50"))

fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

st.caption(LANG["chart_desc"])


# ---------------------------------------------------------
# RSI + MACD
# ---------------------------------------------------------
st.subheader("📊 Indicators")

col1, col2 = st.columns(2)

with col1:
    st.write(f"### {LANG['rsi']}")
    st.line_chart(df.set_index("Date")["RSI"])
    st.caption(LANG["rsi_desc"])

with col2:
    st.write(f"### {LANG['macd']}")
    st.line_chart(df.set_index("Date")[["MACD", "Signal"]])
    st.caption(LANG["macd_desc"])
