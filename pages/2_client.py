import streamlit as st
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
import datetime
# 예시 데이터 로드
url = "https://github.com/hajungg/QAQC1/edit/main/Merged_Dataset_re (1).csv" + '?raw=true'
df_filtered = pd.read_csv(url)

df_filtered = df_filtered.dropna(subset=['ambient_temperature', 'discharge_voltage', 'Rct', 'SOH', 'RUL'])

# 독립 변수(X)와 타겟 변수(y) 설정
X = df_filtered[['ambient_temperature', 'discharge_voltage', 'Rct', 'SOH']]
y = df_filtered['RUL']

# 훈련 데이터와 테스트 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# XGBoost 모델 정의 및 학습
model = XGBRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 스트림릿 인터페이스
st.markdown("<h2 style='text-align: center;'>✨ Chill & NASA RUL 예측 서비스 ✨</h2>", unsafe_allow_html=True)

# 세션 상태 초기화 (누적된 값)
if 'cycle' not in st.session_state:
    st.session_state.cycle = 0  # 싸이클 카운터
    st.session_state.df = pd.DataFrame(columns=['ambient_temperature', 'discharge_voltage', 'Rct', 'SOH', 'RUL'])  # DataFrame 초기화
    st.session_state.rul_predicted = False  # RUL 예측 상태 플래그
    st.session_state.predicted_rul = None  # 예측된 RUL 값 초기화

# 사용자 입력 받기
col1, col2 = st.columns(2)  
with col1:
    ambient_temperature = st.number_input("🌡 온도 (°C)", min_value=-40.0, value=25.0, step=0.1)
    discharge_voltage = st.number_input("🔋 방전 종료 전압 (V)", min_value=0.0, value=3.7, step=0.1)
with col2:
    Rct = st.number_input("⚡ Rct (Ohms)", min_value=0.0, value=0.1, step=0.01)
    SOH = st.number_input("🔧 SOH (%)", min_value=0.0, max_value=100.0, value=100.0, step=0.1)

# "싸이클 완료" 버튼 클릭 시 데이터프레임에 새로운 행 추가하고 예측
predicted_rul = None  
if st.button("🔄 싸이클 완료"):
    st.session_state.cycle += 1
    new_data = {
        'ambient_temperature': ambient_temperature,
        'discharge_voltage': discharge_voltage,
        'Rct': Rct,
        'SOH': SOH
    }
    new_row = pd.DataFrame([new_data])
    st.session_state.df = pd.concat([st.session_state.df, new_row], ignore_index=True)
    
    st.write(f"🔁 현재 싸이클: {st.session_state.cycle} 회")
    st.write("📊 누적 데이터:")
    st.dataframe(st.session_state.df.drop(columns=["RUL"]))  

    if SOH <= 80 and not st.session_state.rul_predicted:
        input_data = st.session_state.df.iloc[-1][['ambient_temperature', 'discharge_voltage', 'Rct', 'SOH']].values.reshape(1, -1)
        st.session_state.predicted_rul = model.predict(input_data)[0]
        st.session_state.rul_predicted = True  
        
        st.markdown(f"<h3 style='color: red;'>🔮 예상 RUL: {st.session_state.predicted_rul:.2f} 회</h3>", unsafe_allow_html=True)
        st.session_state.df.at[st.session_state.df.index[-1], 'RUL'] = st.session_state.predicted_rul

# 하루 평균 사용 시간 입력 후 남은 사용 가능 일수 계산
if st.session_state.predicted_rul is not None:
    CYCLE_DURATION = 10496  
    st.markdown("<h4 style='font-size: 20px;'>⏳ 하루 평균 사용 시간 (초)</h4>", unsafe_allow_html=True)
    daily_usage = st.number_input("", min_value=1, value=36000, step=1)

    if daily_usage > 0:
        remaining_days = (float(st.session_state.predicted_rul) * CYCLE_DURATION) / daily_usage
        annual_replacements = 365 / remaining_days
        BATTERY_PRICE = 5000
        annual_cost = annual_replacements * BATTERY_PRICE

        st.subheader("📅 배터리 사용 예측")
        col5, col6 = st.columns(2)
        with col5:
            st.success(f"📆 남은 사용 가능 일수: **{remaining_days:.2f} 일**")
        with col6:
            st.warning(f"💰 예상 연간 교체 비용: **{annual_cost:,.0f} 원**")

        expected_replacement_date = datetime.date.today() + datetime.timedelta(days=int(remaining_days))
        
        st.subheader("📆 예상 배터리 교체일 (캘린더)")
        calendar_html = f"""
        <html>
        <head>
        <link href='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.css' rel='stylesheet' />
        <script src='https://cdn.jsdelivr.net/npm/fullcalendar@5.10.1/main.min.js'></script>
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var calendarEl = document.getElementById('calendar');
            var calendar = new FullCalendar.Calendar(calendarEl, {{
                initialView: 'dayGridMonth',
                initialDate: '{expected_replacement_date.strftime('%Y-%m-%d')}',
                events: [
                    {{
                        title: '🔋 예상 교체일',
                        start: '{expected_replacement_date.strftime('%Y-%m-%d')}',
                        backgroundColor: '#4CAF50',
                        borderColor: '#388E3C',
                        color: '#FFFFFF'
                    }}
                ]
            }});
            calendar.render();
        }});
        </script>
        </head>
        <body>
        <div id='calendar'></div>
        </body>
        </html>
        """
        st.components.v1.html(calendar_html, height=600)
        st.info(f"📌 예상 배터리 교체일: **{expected_replacement_date.strftime('%Y-%m-%d')}**")
    else:
        st.error("⚠️ 하루 평균 사용 시간은 0보다 커야 합니다!")








  








