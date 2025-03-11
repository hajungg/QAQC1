import streamlit as st
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import itertools
import re

# 페이지 기본 설정

st.markdown("<h2 style='text-align: center;'>✨ Chill & NASA Battery 성능 분석 ✨</h2>", unsafe_allow_html=True)

# 파일 업로드 기능
uploaded_file = st.file_uploader("📂 CSV 파일을 업로드하세요", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.success("✅ 파일 업로드 완료!")


    # EOL 컬럼 체크 및 계산
    if "EOL" not in df.columns:
        df["EOL"] = np.nan
        df["Rct_mean"] = np.nan
        battery_ids = df["battery_id"].unique()

        for battery in battery_ids:
            battery_df = df[df["battery_id"] == battery].copy()
            battery_df.set_index("Cycle", inplace=True)

            if "SOH" not in battery_df.columns or battery_df["SOH"].isna().all():
                df.loc[df["battery_id"] == battery, "EOL"] = "SOH 값이 없어 예측 불가"
                df.loc[df["battery_id"] == battery, "Rct_mean"] = battery_df["Rct"].mean()
                continue

            soh_series = battery_df["SOH"].dropna()
            soh_max = soh_series.max()
            soh_threshold = soh_max * 0.8
            last_cycle = soh_series.index[-1]

            if last_cycle >= 100:
                below_threshold_cycles = soh_series[soh_series.index > soh_series.idxmax()]
                below_threshold_cycles = below_threshold_cycles[below_threshold_cycles <= soh_threshold]
                eol_value = below_threshold_cycles.index[0] if not below_threshold_cycles.empty else "N/A"
            else:
                order = (0, 1, 0)
                seasonal_order = (0, 1, 0, 5)
                model = sm.tsa.statespace.SARIMAX(
                    soh_series, order=order, seasonal_order=seasonal_order,
                    enforce_stationarity=False, enforce_invertibility=False
                )
                results_model = model.fit(disp=False)
                forecast_cycles = np.arange(last_cycle + 1, 101)
                forecast_values = results_model.forecast(steps=len(forecast_cycles))
                predicted_soh_series = pd.Series(forecast_values.values, index=forecast_cycles)
                below_threshold_predicted = predicted_soh_series[predicted_soh_series <= soh_threshold]
                eol_value = f"{below_threshold_predicted.index[0]}(예측)" if not below_threshold_predicted.empty else "N/A"

            rct_mean = battery_df["Rct"].mean()
            df.loc[df["battery_id"] == battery, "EOL"] = eol_value
            df.loc[df["battery_id"] == battery, "Rct_mean"] = rct_mean

    # 빈 컬럼 다시 제거
    df = df.dropna(axis=1, how='all')

    # 데이터 비교 표시
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📋 기존 데이터 미리보기")
        st.dataframe(df.drop(columns=["EOL", "Rct_mean"], errors='ignore').head())

    with col2:
        st.subheader("📊 EOL & Rct_mean 추가된 데이터")
        st.dataframe(df.head())


    # **배터리 성능 지표 & 시험 조건**
    col1, col2 = st.columns(2, gap="medium")

    with col1:
        st.subheader("🔋 Battery 성능지표")
        selected_battery_1 = st.selectbox("Battery ID 선택 (성능 지표)", df["battery_id"].unique(), key="battery_1")
        battery_1cycle_data_1 = df[(df["battery_id"] == selected_battery_1) & (df["Cycle"] == 1)]

        if not battery_1cycle_data_1.empty:
            eol_value = battery_1cycle_data_1["EOL"].values[0]
            rct_mean_value = battery_1cycle_data_1["Rct_mean"].values[0]

            st.markdown(
                f"""
                <div style="background-color:#E8F5E9; padding:15px; border-radius:10px; margin-bottom:20px;">
                    <b>EOL:</b> {eol_value} cycle
                </div>
                <div style="background-color:#E8F5E9; padding:15px; border-radius:10px; margin-bottom:20px;">
                    <b>Rct Median:</b> {rct_mean_value}Ω
                </div>
                """, unsafe_allow_html=True
            )

    with col2:
        st.subheader("🧪 Battery 시험 조건")
        selected_battery_2 = st.selectbox("Battery ID 선택 (시험 조건)", df["battery_id"].unique(), key="battery_2")
        battery_1cycle_data_2 = df[(df["battery_id"] == selected_battery_2) & (df["Cycle"] == 1)]

        if not battery_1cycle_data_2.empty:
            temp_value = battery_1cycle_data_2["ambient_temperature"].values[0]
            charge_current = battery_1cycle_data_2["charge_current(A)"].values[0]
            discharge_current = battery_1cycle_data_2["discharge_current(A)"].values[0]
            discharge_voltage = battery_1cycle_data_2["discharge_voltage(V)"].values[0]

            col1_1, col1_2 = st.columns(2)
            col2_1, col2_2 = st.columns(2)

            with col1_1:
                st.markdown(f"<div style='background-color:#E8F5E9; padding:15px; border-radius:10px; margin-bottom:10px;'><b>Temperature:</b> {temp_value} °C</div>", unsafe_allow_html=True)
            with col1_2:
                st.markdown(f"<div style='background-color:#E8F5E9; padding:15px; border-radius:10px; margin-bottom:10px;'><b>CC Current(충전):</b> {charge_current} A</div>", unsafe_allow_html=True)
            with col2_1:
                st.markdown(f"<div style='background-color:#E8F5E9; padding:15px; border-radius:10px; margin-bottom:10px;'><b>CC Current(방전):</b> {discharge_current} A</div>", unsafe_allow_html=True)
            with col2_2:
                st.markdown(f"<div style='background-color:#E8F5E9; padding:15px; border-radius:10px; margin-bottom:10px;'><b>CC Cut-off(방전):</b> {discharge_voltage} V</div>", unsafe_allow_html=True)

    # **Battery EOL & SOH 그래프 추가**
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Battery EOL")
        battery_options = ["전체"] + list(df["battery_id"].unique())
        selected_batteries_eol = st.multiselect("Battery ID 선택", battery_options, default=["전체"], key="battery_eol")

        if "전체" in selected_batteries_eol:
            eol_data = df[df["Cycle"] == 1][["battery_id", "EOL"]]
        else:
            eol_data = df[df["battery_id"].isin(selected_batteries_eol) & (df["Cycle"] == 1)][["battery_id", "EOL"]]

        if not eol_data.empty:
            eol_data["EOL"] = eol_data["EOL"].astype(str).apply(lambda x: int(re.search(r'\d+', x).group()) if re.search(r'\d+', x) else 0)
            fig, ax = plt.subplots(figsize=(6, 4))
            bars = ax.bar(eol_data["battery_id"].astype(str), eol_data["EOL"], color="lightgreen")
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2, height, f"{height}", ha='center', va='bottom', fontsize=10)
            
            ax.set_xlabel("Battery ID")
            ax.set_ylabel("EOL")
            ax.set_title("Battery EOL")
            ax.set_xticks(range(len(eol_data["battery_id"])))
            ax.set_xticklabels(eol_data["battery_id"].astype(str))
            st.pyplot(fig)

    with col2:
        st.subheader("📉 Battery SOH & Rct")
        selected_batteries_soh = st.multiselect("Battery ID 선택", battery_options, default=["전체"], key="battery_soh")

        if "전체" in selected_batteries_soh:
            filtered_df = df
        else:
            filtered_df = df[df["battery_id"].isin(selected_batteries_soh)]

        if not filtered_df.empty:
            fig, ax1 = plt.subplots(figsize=(6, 4))
            ax2 = ax1.twinx()

            colors = itertools.cycle(plt.rcParams["axes.prop_cycle"].by_key()["color"])
            battery_colors = {battery: next(colors) for battery in filtered_df["battery_id"].unique()}

            for battery in filtered_df["battery_id"].unique():
                battery_data = filtered_df[filtered_df["battery_id"] == battery]
                color = battery_colors[battery]
                
                if "SOH" in battery_data and battery_data["SOH"].notna().any():
                    ax1.plot(battery_data["Cycle"], battery_data["SOH"], label=f"{battery} SOH", linestyle="-", color=color)
                if "Rct" in battery_data and battery_data["Rct"].notna().any():
                    ax2.plot(battery_data["Cycle"], battery_data["Rct"], label=f"{battery} Rct", linestyle="--", color=color)

            ax1.set_xlabel("Cycle")
            ax1.set_ylabel("SOH")
            ax2.set_ylabel("Rct")
            ax1.set_title("Battery SOH & Rct")
            
            fig.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3)
            st.pyplot(fig)
        else:
            st.warning("⚠️ 선택한 필터에 해당하는 데이터가 없습니다.")



    # 두 개의 컬럼 생성 (동일한 행에서 시작)
    col1, col2 = st.columns(2, gap="large")

    with st.container():
        with col1:
            st.subheader("📈 모니터링 (1) - Time vs. Voltage")
        with col2:
            st.subheader("📊 모니터링 (2)")

    # 모니터링 (1) - Time vs. Voltage
    with col1:
        file_1 = st.file_uploader("📂 CSV 파일을 업로드하세요 (Time vs. Voltage 분석)", type=["csv"], key="file1")
        
        if file_1:
            df1 = pd.read_csv(file_1)
            st.success("✅ 파일 업로드 완료!")
            
            required_columns_1 = {"battery_id", "cycle", "Time", "Voltage_measured", "type"}
            if not required_columns_1.issubset(df1.columns):
                st.error("🚨 파일에 'battery_id', 'cycle', 'Time', 'Voltage_measured', 'type' 컬럼이 포함되어야 합니다.")
                st.stop()
            
            # 필터링 요소를 한 줄에 배치
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                selected_batteries = st.multiselect("Battery ID 선택", df1["battery_id"].unique(), key="monitoring1")
            with col_f2:
                selected_types = st.multiselect("Type 선택", df1["type"].unique(), key="type1")
            with col_f3:
                all_cycles = ["전체"] + sorted(df1["cycle"].unique())
                selected_cycles = st.multiselect("Cycle 선택", all_cycles, key="cycle1")
            
            if "전체" in selected_cycles:
                selected_cycles = df1["cycle"].unique()
            
            filtered_df = df1[
                (df1["battery_id"].isin(selected_batteries)) &
                (df1["type"].isin(selected_types)) &
                (df1["cycle"].isin(selected_cycles))
            ]
            
            if not filtered_df.empty:
                fig, ax = plt.subplots()
                colors = {"charge": "blue", "discharge": "red"}
                
                for cycle in sorted(filtered_df["cycle"].unique()):
                    cycle_data = filtered_df[filtered_df["cycle"] == cycle]
                    color_intensity = cycle / max(df1["cycle"])  # 사이클이 증가할수록 색 진하게
                    
                    for t in cycle_data["type"].unique():
                        subset = cycle_data[cycle_data["type"] == t]
                        ax.scatter(subset["Time"], subset["Voltage_measured"], 
                                color=colors[t], alpha=color_intensity, label=f"{t} - Cycle {cycle}")
                
                ax.set_xlabel("Time")
                ax.set_ylabel("Voltage_measured")
                ax.set_title("Time vs. Voltage")
                ax.legend()
                st.pyplot(fig)
            else:
                st.info("🔍 배터리 ID, Type, Cycle을 선택해주세요.")
        else:
            st.warning("⚠️ 파일을 업로드해주세요.")

    # 모니터링 (2)
    with col2:
        file_2 = st.file_uploader("📂 CSV 파일을 업로드하세요 (유연한 분석)", type=["csv"], key="file2")
        
        if file_2:
            df2 = pd.read_csv(file_2)
            st.success("✅ 파일 업로드 완료!")
            
            # 필터링 요소를 한 줄에 배치, 독립적인 키 사용
            col_f1, col_f2, col_f3 = st.columns(3)
            
            with col_f1:
                selected_battery_2 = st.selectbox("Battery ID 선택", df2["battery_id"].unique(), key="monitoring2_independent")
            with col_f2:
                x_axis = st.selectbox("X축 설정", df2.columns, key="x_axis_independent")
            with col_f3:
                y_axis = st.selectbox("Y축 설정", df2.columns, key="y_axis_independent")
            
            if selected_battery_2 and x_axis and y_axis:
                plot_data = df2[df2["battery_id"] == selected_battery_2]
                
                fig, ax = plt.subplots()
                ax.plot(plot_data[x_axis], plot_data[y_axis], marker='o', linestyle='-')
                ax.set_xlabel(x_axis)
                ax.set_ylabel(y_axis)
                ax.set_title(f"{selected_battery_2} - {x_axis} vs. {y_axis}")
                st.pyplot(fig)
            else:
                st.info("🔍 배터리 ID, X축, Y축을 선택해주세요.")
        else:
            st.warning("⚠️ 파일을 업로드해주세요.")
