import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# --------------------------
# UI CONFIG
# --------------------------
st.set_page_config(page_title="AI Stock Advisor", layout="wide")
st.title("📈 AI Stock Advisor – ระบบช่วยตัดสินใจซื้อขายหุ้น")

st.write("""
ระบบนี้ช่วยวิเคราะห์แนวโน้มตลาดจากอินดิเคเตอร์มาตรฐาน เช่น  
**SMA, RSI, MACD** และตัดสินใจให้เป็น **ซื้อ / ถือ / ขาย** โดยอิงตามความสมเหตุสมผลทางเทคนิค
""")

# --------------------------
# STOCK SELECTOR (NEW!)
# --------------------------

st.subheader("🔍 เลือกหุ้นที่ต้องการวิเคราะห์")

popular_stocks = {
    "🇺🇸 หุ้นอเมริกา": ["AAPL", "MSFT", "AMZN", "NVDA", "META", "TSLA", "GOOGL"],
    "🇹🇭 หุ้นไทย": ["PTT", "AOT", "CPALL", "KBANK", "ADVANC", "SCB", "BDMS"],
    "📈 Crypto": ["BTC-USD", "ETH-USD", "BNB-USD"]
}

colA, colB = st.columns([2,1])

with colA:
    ticker = st.text_input(
        "พิมพ์ชื่อหุ้น (Ticker Symbol)",
        value="AAPL",
        help="เช่น AAPL = Apple, MSFT = Microsoft, PTT = ปตท."
    )

with colB:
    category = st.selectbox("เลือกจากหมวดหมู่", list(popular_stocks.keys()))
    from_list = st.selectbox("ตัวเลือกหุ้นยอดนิยม", popular_stocks[category])
    if st.button("ใช้ตัวเลือกนี้"):
        ticker = from_list


period = st.selectbox("ช่วงเวลา", ["3mo", "6mo", "1y", "2y", "5y"], index=2)


# --------------------------
# INDICATOR GUIDE (NEW!)
# --------------------------

with st.expander("📘 คำอธิบาย โปรดกดอ่านเพื่อเข้าใจถึงการพิจารณา"):
    st.markdown("""
### ⭐ SMA (Simple Moving Average)
- SMA20 = ค่าเฉลี่ยราคาปิด 20 วัน  
- SMA50 = ค่าเฉลี่ยราคาปิด 50 วัน  
**ใช้ดูแนวโน้มระยะสั้นและกลาง**  
- ถ้า SMA20 > SMA50 → แนวโน้มขึ้น  
- ถ้า SMA20 < SMA50 → แนวโน้มลง  

---

### ⭐ RSI (Relative Strength Index)
ใช้ดูว่าแรงซื้อแรงขายมากเกินไปหรือไม่  
- RSI > 70 → Overbought (เสี่ยงลง)  
- RSI < 30 → Oversold (เสี่ยงขึ้น)  

---

### ⭐ MACD
ใช้ดูโมเมนตัมตลาด  
- MACD ตัดขึ้น Signal → แนวโน้มบวก  
- MACD ตัดลง → แนวโน้มลบ
    """)

# --------------------------
# LOAD DATA
# --------------------------

@st.cache_data
def load_stock(symbol, period):
    df = yf.download(symbol, period=period, auto_adjust=True)
    df.reset_index(inplace=True)
    return df

df = load_stock(ticker, period)
df.columns = df.columns.get_level_values(0)

if df.empty:
    st.error("❌ ไม่พบข้อมูลหุ้น กรุณาตรวจสอบชื่อให้ถูกต้อง")
    st.stop()

# --------------------------
# CALCULATE INDICATORS
# --------------------------

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

# --------------------------
# AI DECISION
# --------------------------

def decision_engine(df):
    latest = df.iloc[-1]
    score = 50
    reasons = []

    if latest["SMA20"] > latest["SMA50"]:
        score += 15
        reasons.append("📈 SMA20 > SMA50 → แนวโน้มระยะกลางเป็นขาขึ้น")
    else:
        score -= 15
        reasons.append("📉 SMA20 < SMA50 → เทรนด์เริ่มอ่อนแรง")

    if latest["RSI"] < 30:
        score += 20
        reasons.append("🟢 RSI < 30 → Oversold มีโอกาสเด้ง")
    elif latest["RSI"] > 70:
        score -= 20
        reasons.append("🔴 RSI > 70 → Overbought มีโอกาสลง")

    if latest["MACD"] > latest["Signal"]:
        score += 15
        reasons.append("📈 MACD ตัดขึ้น Signal → โมเมนตัมดี")
    else:
        score -= 15
        reasons.append("📉 MACD ตัดลง → ความแข็งแรงลดลง")

    if latest["Close"] > latest["SMA50"]:
        score += 10
        reasons.append("💵 ราคายืนเหนือ SMA50 → ตลาดแข็งแรง")
    else:
        score -= 10
        reasons.append("⚠️ ราคาต่ำกว่า SMA50 → ความเสี่ยงเพิ่ม")

    score = max(0, min(100, score))

    if score >= 70:
        decision = "🟢 แนะนำ: ซื้อ (Strong Buy)"
    elif score >= 55:
        decision = "🟡 แนะนำ: ถือ (Hold)"
    else:
        decision = "🔴 แนะนำ: ขาย (Sell)"

    return score, decision, reasons

score, decision, reasons = decision_engine(df)

# --------------------------
# DECISION OUTPUT
# --------------------------
st.subheader("🔍 ผลการวิเคราะห์ AI")

st.metric("คะแนนแนวโน้ม", f"{score}/100")

if "ซื้อ" in decision:
    st.success(decision)
elif "ขาย" in decision:
    st.error(decision)
else:
    st.warning(decision)

with st.expander("📌 เหตุผลของการวิเคราะห์ AI"):
    for r in reasons:
        st.write("• " + r)


# --------------------------
# PRICE CHART
# --------------------------
st.subheader("📈 กราฟราคา + เส้นแนวโน้ม")

fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=df["Date"],
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="ราคา"
))

fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA20"], name="SMA20", line=dict(width=1)))
fig.add_trace(go.Scatter(x=df["Date"], y=df["SMA50"], name="SMA50", line=dict(width=1)))

fig.update_layout(height=500)
st.plotly_chart(fig, use_container_width=True)

with st.expander("ℹ️ คำอธิบายกราฟ"):
    st.write("""
- **Candlestick** = ราคา  
- **SMA20** = แนวโน้มระยะสั้น  
- **SMA50** = แนวโน้มระยะกลาง  
ถ้า SMA20 ตัดขึ้น SMA50 → สัญญาณดี  
    """)

# --------------------------
# RSI & MACD CHART
# --------------------------

st.subheader("📊 ตัวชี้วัดเพิ่มเติม")

col1, col2 = st.columns(2)

with col1:
    st.write("### RSI")
    st.line_chart(df.set_index("Date")["RSI"])
    st.caption("RSI > 70 = Overbought | RSI < 30 = Oversold")

with col2:
    st.write("### MACD")
    st.line_chart(df.set_index("Date")[["MACD", "Signal"]])
    st.caption("MACD ตัดขึ้น Signal = ขาขึ้น | ตัดลง = ขาลง")
