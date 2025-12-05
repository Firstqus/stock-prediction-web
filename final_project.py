import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import date, timedelta
from prophet import Prophet
from prophet.plot import plot_plotly

try:
    nltk.data.find('vader_lexicon')
except LookupError:
    nltk.download('vader_lexicon')
#-----Fornt web-----
#ชื่อเว็ป
st.set_page_config(page_title="Stock Prophet", page_icon = "📈" , layout = "wide")
#sidebar ซ้ายมือ
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5381/5381282.png", width = 100)
st.sidebar.header("Setting Predict")


selected_stock = st.sidebar.text_input('Ticker Symbol', 'TSLA')
n_years = st.sidebar.slider('ดูข้อมูลย้อนหลัง(ปี):',1 , 5 , 3)
period = n_years *  365
st.sidebar.markdown("---")
st.sidebar.write("Developed by **Student**")

#data loading
@st.cache_data
def load_data(ticker):
    data = yf.download(ticker, start=date.today()-timedelta(days=period), end=date.today())
    #fixedbug
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.get_level_values(0)
    data.reset_index(inplace=True)
    return data
with st.spinner("loding data..."):
    data = load_data(selected_stock)
if data.empty:
    st.error(f"❌ ไม่พบข้อมูลหุ้น: {selected_stock}")
    st.warning("สาเหตุที่เป็นไปได้: 1. พิมพ์ชื่อหุ้นผิด 2. ตลาดปิด/วันหยุด 3. Yahoo Finance บล็อกการเข้าถึงจาก Cloud ชั่วคราว")
    st.stop() # 🛑 สั่งหยุดทำงานทันที ไม่ให้ไปรันบรรทัดถัดไป (กัน Error)

data["SMA50"] = data['Close'].rolling(window=50).mean()
data["SMA200"] = data['Close'].rolling(window=200).mean()

#Main dashboard
#name stock/price
col1, col2 = st.columns([1,3])
with col1:
    st.title(f"📊 {selected_stock}")
with col2:
    #price
    last_price = data["Close"].iloc[-1]
    prev_price = data["Close"].iloc[-2]
    change = last_price - prev_price
    pct_change = (change / prev_price) * 100

    #add matrix 
    st.metric(label="ราคาล่าสุด (Close price)",
              value=f"{last_price:.2f}",
              delta=f"{change:.2f} ({pct_change:.2f}%)")
#create tap
tab1 , tab2 , tab3 , tab4= st.tabs(["📈 ภาพรวม (Technical)", "ทำนายอนาคต (Forecast)", "ข้อมูลดิบ (Raw data)", "📰 วิเคราะห์ข่าว (News AI)"])
#Techninal Analysis
with tab1:
    st.subheader(f"กราฟราคาเส้นแนวโน้ม (SMA)")

    #custom graph plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['Date'], y = data["Close"], name="Close Price", line_color='#1f77b4' ))
    fig.add_trace(go.Scatter(x=data['Date'], y = data["SMA50"], name="SMA 50 (short term)",line_color = "#9467bd", line=dict(width=2)))
    fig.add_trace(go.Scatter(x=data['Date'], y = data["SMA200"], name ="SMA200 (longterm)", line_color = "#ff7f0e", line=dict(width=2)))
    fig.layout.update(
        xaxis_rangeslider_visible=True,
        height=500,
        template="plotly_dark",
        margin=dict(l=20, r=20, t=50, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)


    #comment signals
    st.info("💡 **Tips:** ถ้าเส้น SMA50 (สีม่วง) ตัดขึ้นเหนือ SMA200 (สีส้ม) เรียกว่า 'Golden Cross' เป็นสัญญาณขาขึ้น")
with tab2:
    st.subheader(f"แนวโน้มราคาในอีก {n_years} ปีข้างหน้า (AI Forecast)")
    #prophet data
    df_train = data[["Date", "Close"]].rename(columns={"Date":'ds','Close':'y'})
    m = Prophet()
    m.fit(df_train)
    future = m.make_future_dataframe(periods=period)
    forecast = m.predict(future)

    #graph predict
    fig_pred = plot_plotly(m, forecast)
    fig_pred.update_layout(height=500, template="plotly_dark", xaxis_rangeslider_visible=True)
    st.plotly_chart(fig_pred, use_container_width=True)
    
    # กราฟ Components (แยกส่วน)
    st.write("---")
    st.write("##### 🧩 เจาะลึกพฤติกรรมราคา (Components)")
    col_a, col_b = st.columns(2)
    
    # ต้องดึงกราฟจาก matplotlib มาโชว์
    fig_comp = m.plot_components(forecast)
    st.pyplot(fig_comp)

# --- TAB 3: Raw Data ---
with tab3:
    st.subheader("ข้อมูลราคาหุ้นย้อนหลัง")
    st.dataframe(data.sort_values(by='Date', ascending=False), use_container_width=True)
with tab4:
    st.subheader(f"ข่าวล่าสุดของ {selected_stock} และ AI predict")
    #news pulled from Yahoo Finance
    sn = yf.Ticker(selected_stock)
    news_list = sn.news
    #Analyzer
    sia = SentimentIntensityAnalyzer()
# 3. วนลูปอ่านข่าว (แก้บั๊ก NoneType เรียบร้อย)
    for i in news_list:
        # 1. เช็คก่อนว่ามีกุญแจชื่อ 'content' ไหม
        if 'content' in i:
            payload = i['content']
            
            title = payload.get('title', 'ไม่ระบุหัวข้อข่าว')
            
            # --- แก้ตรงนี้: เช็คก่อนดึงลิงก์ ---
            click_url = payload.get('clickThroughUrl')
            if click_url: # ถ้ามีข้อมูล (ไม่เป็น None)
                link = click_url.get('url', '#')
            else:
                link = '#'
            # -------------------------------
            
            # --- แก้ตรงนี้: เช็คก่อนดึงสำนักข่าว ---
            provider = payload.get('provider')
            if provider:
                publisher = provider.get('displayName', 'Unknown')
            else:
                publisher = 'Unknown'
            # -------------------------------
            
        # 2. เผื่อฟลุ๊คเจอแบบเก่า (Title อยู่ชั้นนอกสุด)
        else:
            title = i.get('title', 'ไม่ระบุหัวข้อข่าว')
            link = i.get('link', '#')
            publisher = i.get('publisher', 'Unknown')

        # ถ้าหาหัวข้อไม่เจอจริงๆ ให้ข้าม
        if title == 'ไม่ระบุหัวข้อข่าว':
            continue

        # --- ส่วนคำนวณ AI (เหมือนเดิม) ---
        try:
            score = sia.polarity_scores(title)['compound']
        except:
            score = 0 

        # --- ส่วนเลือกสี (เหมือนเดิม) ---
        if score > 0.05:
            sentiment = "Bullish (ข่าวดี) 🐂"
            color = "#00FF00"
        elif score < -0.05:
            sentiment = "Bearish (ข่าวร้าย) 🐻"
            color = "#FF4B4B"
        else:
            sentiment = "Neutral (เฉยๆ) 😐"
            color = "gray"
            
        # --- ส่วนแสดงผล HTML (เหมือนเดิม) ---
        st.markdown(f"""
        <div style="padding: 10px; border-radius: 5px; border: 1px solid #333; margin-bottom: 10px;">
            <h4 style="color: {color}; margin:0;">{sentiment} (Score: {score:.2f})</h4>
            <a href="{link}" target="_blank" style="text-decoration: none; color: white;">
                <h3>{title}</h3>
            </a>
            <small>Source: {publisher}</small>
        </div>
        """, unsafe_allow_html=True)