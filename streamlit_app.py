# app.py
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests

st.set_page_config(page_title="물러서는 땅, 다가오는 바다", layout="wide")
st.title("🌊 물러서는 땅, 다가오는 바다 — 피해, 인식, 지도 시각화")

# -----------------------
# 국가별 피해 사례 및 대처 방안
# -----------------------
country_info = {
    "투발루": {
        "피해": "평균 해발 2~3m로 해수면 상승에 가장 취약합니다. 농경지와 식수원 침수, 환경 난민 발생 사례가 있습니다.",
        "대처": ["국제 사회에 이민 요청", "기후변화 협약에서 생존권 보장 요구"]
    },
    "방글라데시": {
        "피해": "매년 우기마다 농경지가 침수되어 수백만 명의 주민 생계가 위협받습니다.",
        "대처": ["홍수 방지 제방 건설", "기후 난민 이주 정책 논의"]
    },
    "몰디브": {
        "피해": "일부 섬이 바닷물에 잠겨 거주 불가능 지역이 증가하고 있습니다.",
        "대처": ["관광 수익으로 해안 방어 시설 건설", "산호초 복원 프로젝트"]
    },
    "네덜란드": {
        "피해": "저지대 국가 특성상 해수면 상승에 직접적인 위협을 받습니다.",
        "대처": ["세계 최고 수준의 방조제와 수문 시스템 운영"]
    },
    "미국 마이애미": {
        "피해": "‘Sunny Day Flooding’ 현상으로 도로가 주기적으로 침수됩니다.",
        "대처": ["해안 방어벽 설치", "빗물 배수 시스템 강화"]
    },
    "인도네시아 자카르타": {
        "피해": "해수면 상승과 지반 침하로 도심 침수가 심각합니다. 수도 이전 논의가 있습니다.",
        "대처": ["수도 이전(누산타라 건설)", "대규모 해안 방조제 건설"]
    }
}

# -----------------------
# 사용자 입력
# -----------------------
col1, col2 = st.columns([2,1])
with col1:
    place_input = st.text_input("🔎 국가 또는 도시 입력 (예: 투발루, 베네치아, 다카)")
with col2:
    year_input = st.number_input("◀ 과거 연도 선택 (1800~2024)", min_value=1800, max_value=2024, value=1900, step=1)

# -----------------------
# 간단 모델 (교육용)
# -----------------------
@st.cache_data
def get_global_sea_level_rise_m(year):
    now = 2025
    total_since_1880_m = 0.25
    if year >= 1880:
        frac = (year - 1880) / (now - 1880)
        return frac * total_since_1880_m
    else:
        return (year - 1800) / (1880 - 1800) * (total_since_1880_m * 0.2)

@st.cache_data
def get_global_temperature_anomaly_c(year):
    now = 2025
    current = 1.5
    if year >= 1900:
        frac = (year - 1900) / (now - 1900)
        return frac * current
    elif year >= 1850:
        return (year - 1850) / (1900 - 1850) * (current * 0.5)
    else:
        return (year - 1800) / (1850 - 1800) * (current * 0.2)

# -----------------------
# 지오코딩
# -----------------------
def geocode_city(city_name):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city_name, "format": "json", "limit": 1}
        headers = {"User-Agent": "sea-level-app/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        data = resp.json()
        if len(data) > 0:
            item = data[0]
            return float(item["lat"]), float(item["lon"]), item["display_name"]
    except:
        return None, None, None
    return None, None, None

# -----------------------
# 조회 및 출력
# -----------------------
if st.button("🔍 조회 및 지도 표시"):
    if not place_input.strip():
        st.error("장소 이름을 입력해주세요.")
    else:
        lat, lon, display = geocode_city(place_input)
        if lat is None:
            st.error("해당 장소를 찾을 수 없습니다.")
        else:
            st.subheader(f"📍 {display} 정보")
            
            # 피해 사례
            country = display.split(",")[-1].strip()
            impact_text = country_info.get(country, {}).get("피해", "해당 지역 피해 정보 없음.")
            st.markdown(f"**피해 사례:** {impact_text}")
            
            # 대처 방안 체크박스
            st.subheader("🛠 대처 방안")
            actions = country_info.get(country, {}).get("대처", [])
            selected_actions = []
            for a in actions:
                if st.checkbox(a):
                    selected_actions.append(a)
            if selected_actions:
                st.success(f"✅ 선택한 대처 방안: {', '.join(selected_actions)}")
            
            # 해수면 상승/온도 정보
            past_sl = get_global_sea_level_rise_m(year_input)
            now_sl = get_global_sea_level_rise_m(2025)
            diff_sl = now_sl - past_sl
            past_temp = get_global_temperature_anomaly_c(year_input)
            now_temp = get_global_temperature_anomaly_c(2025)
            diff_temp = now_temp - past_temp
            
            st.markdown(f"- **{year_input} 전지구 평균 해수면 상승 근사:** {past_sl:.3f} m")
            st.markdown(f"- **2025 전지구 평균 해수면 상승 근사:** {now_sl:.3f} m")
            st.markdown(f"- **차이:** {diff_sl:.3f} m")
            st.markdown(f"- **{year_input} 전지구 평균 온도 이상치 근사:** {past_temp:.2f}°C")
            st.markdown(f"- **2025 전지구 평균 온도 이상치 근사:** {now_temp:.2f}°C")
            st.markdown(f"- **차이:** {diff_temp:.2f}°C")
            
            # 해수면 상승 인식 조사
            st.subheader("💡 해수면 상승 인식 조사")
            q1 = st.checkbox("해수면 상승이 지구에 큰 영향을 준다는 사실을 알고 있다.")
            q2 = st.checkbox("내 주변 국가 또는 도시도 해수면 상승 영향을 받을 수 있다고 생각한다.")
            q3 = st.checkbox("기후 변화와 해수면 상승 문제에 대해 더 배우고 싶다.")
            score = sum([q1,q2,q3])
            st.markdown(f"✔ 체크 개수: {score}/3")
            
            # 의견 입력
            st.subheader("📝 해수면 상승 대응 아이디어 또는 의견")
            user_idea = st.text_area("의견 입력")
            if user_idea:
                st.info(f"💬 제출 의견: {user_idea}")
            
            # -----------------------
            # 지도 시각화 (세계 지도 + 바다 온도 상승 표시 + 위치 화살표)
            # -----------------------
            st.subheader("🗺️ 세계 지도 시각화 (바다 온도 상승 색상, 2025 기준)")
            
            # 교육용 임의 데이터 생성 (바다 온도 변화 근사)
            lats = np.linspace(-90,90,36)
            lons = np.linspace(-180,180,72)
            temp_data = []
            for lat in lats:
                for lon in lons:
                    temp_val = np.sin(np.radians(lat))*2 + np.random.uniform(-0.5,0.5)
                    temp_data.append({"lat": lat, "lon": lon, "temp": temp_val})
            temp_df = pd.DataFrame(temp_data)
            
            # Heatmap Layer
            heat_layer = pdk.Layer(
                "HeatmapLayer",
                data=temp_df,
                get_position='[lon, lat]',
                get_weight="temp",
                radiusPixels=20,
                intensity=1,
                threshold=0.01,
            )
            
            # 위치 화살표 Layer
            icon
