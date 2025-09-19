import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests

st.set_page_config(page_title="물러서는 땅, 다가오는 바다", layout="wide")

st.title("🌍 해수면ㆍ기온 변화 비교 시뮬레이터")

# --- 입력: 지역 + 과거 연도 ---
search_term = st.text_input("도시 또는 지역 이름을 입력하세요 (예: Incheon, Tokyo, London)", "")
year_input = st.number_input("비교할 과거 연도 입력 (예: 1800 ~ 2024)", min_value=1800, max_value=2024, value=1900, step=1)

def geocode_city(city_name):
    """도시 이름 → 위도/경도로 변환 (Nominatim API)"""
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={city_name}"
    resp = requests.get(url, headers={"User-Agent": "streamlit-app"})
    if resp.status_code == 200 and len(resp.json()) > 0:
        loc = resp.json()[0]
        return float(loc["lat"]), float(loc["lon"]), loc["display_name"]
    return None, None, None

@st.cache_data
def get_global_sea_level_rise(year):
    """
    연도 기준으로 현재(또는 최근년) 대비 전지구 평균 해수면 상승 추정치 반환
    단, 1800~1880 이전은 proxy data 기반 추정치
    """
    current_rise_cm = 25.0  # 1880 ~ 지금까지 약 25cm 상승
    if year >= 1880:
        now = pd.Timestamp.now().year
        fraction = (year - 1880) / (now - 1880)
        past_rise = fraction * current_rise_cm
    else:
        # 1800~1880 구간: 작은 값으로 보간
        past_rise = (year - 1800) / (1880 - 1800) * (current_rise_cm * 0.2)
    return past_rise / 100.0  # m 단위

@st.cache_data
def get_global_temperature_anomaly(year):
    """
    연도 기준으로 과거 대비 온도 차이 (pre-industrial 대비)
    """
    current_anomaly = 1.5  # 현재는 약 +1.5°C
    if year >= 1900:
        now = pd.Timestamp.now().year
        fraction = (year - 1900) / (now - 1900)
        past_anom = fraction * current_anomaly
    elif year >= 1850:
        past_anom = (year - 1850) / (1900 - 1850) * (current_anomaly * 0.5)
    else:
        past_anom = (year - 1800) / (1850 - 1800) * (current_anomaly * 0.2)
    return past_anom

if st.button("비교하기"):
    if not search_term.strip():
        st.error("먼저 지역 이름을 입력해주세요.")
    else:
        lat, lon, full_name = geocode_city(search_term)
        if lat is None:
            st.error(f"'{search_term}' 위치를 찾을 수 없습니다. 영어/한글 이름 확인해주세요.")
        else:
            st.success(f"'{full_name}' 위치를 탐지했습니다.")

            # 과거 vs 현재 해수면 상승
            past_sl_m = get_global_sea_level_rise(year_input)
            now_sl_m = get_global_sea_level_rise(pd.Timestamp.now().year)
            diff_sl = now_sl_m - past_sl_m

            # 과거 vs 현재 기온 이상치
            past_temp = get_global_temperature_anomaly(year_input)
            now_temp = get_global_temperature_anomaly(pd.Timestamp.now().year)
            diff_temp = now_temp - past_temp

            st.write(f"## 비교 결과: {full_name} / {year_input} vs 현재")

            st.metric(label=f"{year_input} 해수면 상승 (글로벌 평균)", value=f"{past_sl_m:.3f} m")
            st.metric(label="현재 해수면 상승 (글로벌 평균)", value=f"{now_sl_m:.3f} m")
            st.metric(label="두 시점 간 해수면 차이", value=f"{diff_sl:.3f} m")

            st.write("---")

            st.metric(label=f"{year_input} 기온 이상치 (pre-industrial 대비)", value=f"{past_temp:.2f} °C")
            st.metric(label="현재 기온 이상치 (pre-industrial 대비)", value=f"{now_temp:.2f} °C")
            st.metric(label="두 시점 간 기온 차이", value=f"{diff_temp:.2f} °C")

            # 지도 표시
            view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=6, pitch=0)
            df_pt = pd.DataFrame([{"lat": lat, "lon": lon, "color": [0, 114, 178]}])
            layer = pdk.Layer(
                "ScatterplotLayer", data=df_pt, get_position='[lon, lat]',
                get_color='color', get_radius=50000
            )
            r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="light")
            st.pydeck_chart(r)

            # --- 📌 출처 + 대처 방안 + 투발루 사례 ---
            st.write("---")
            st.subheader("📚 데이터 출처")
            st.markdown("""
            - Our World in Data: [Global mean sea levels since 1880](https://ourworldindata.org/data-insights/global-mean-sea-levels-have-increased-by-around-25-centimeters-since-1880)
            - EEA (European Environment Agency): [Global and European sea level rise](https://www.eea.europa.eu/en/analysis/indicators/global-and-european-sea-level-rise)
            - NASA Climate: [Global Temperature Vital Signs](https://climate.nasa.gov/vital-signs/global-temperature/)
            - OpenStreetMap Nominatim API (위치 검색)
            """)

            st.subheader("🌱 기후 위기 대처 방안")
            st.markdown("""
            - **탄소 배출 감축**: 재생에너지 확대, 화석연료 사용 최소화  
            - **기후 적응 정책**: 방조제 건설, 해안선 관리, 도시계획 개선  
            - **국제 협력**: 파리협정 등 글로벌 협약 강화  
            - **개인 실천**: 대중교통 이용, 에너지 절약, 식생활 개선 등  
            """)

            st.subheader("🌊 해수면 상승 피해 사례 – 투발루")
            st.markdown("""
            남태평양의 작은 섬나라 **투발루(Tuvalu)**는 평균 해발고도가 불과 2m 남짓으로,  
            해수면 상승의 직접적인 위협을 받고 있습니다.  
            실제로 해수면 상승과 폭풍우로 인해 **토지가 잠기고 식수가 오염**되며,  
            주민들은 국토 자체가 사라질 위기에 처해 있습니다.  
            이로 인해 투발루는 국제사회에 기후난민 문제와 지구 공동 대응의 필요성을 강하게 호소하고 있습니다.  
            """)
