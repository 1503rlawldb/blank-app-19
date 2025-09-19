# app.py
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests
from math import cos, sin, pi

# -----------------------
# 페이지 설정
# -----------------------
st.set_page_config(page_title="물러서는 땅, 다가오는 바다 — 비교 시뮬레이터", layout="wide")
st.title("🌊 물러서는 땅, 다가오는 바다 — 연도별 해수면 비교 & 시각화")

# -----------------------
# 지오코딩
# -----------------------
def geocode_city(city_name):
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": city_name, "format": "json", "limit": 1}
        headers = {"User-Agent": "sea-level-app/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if len(data) > 0:
            item = data[0]
            return float(item["lat"]), float(item["lon"]), item["display_name"]
    except:
        st.error("지오코딩 실패. 장소 이름을 확인해주세요.")
    return None, None, None

# -----------------------
# 교육용 해수면 상승/온도 계산
# -----------------------
@st.cache
def get_global_sea_level_rise_m(year):
    now = 2025
    total_since_1880_m = 0.25
    if year >= 1880:
        frac = (year - 1880) / (now - 1880)
        return frac * total_since_1880_m
    else:
        return (year - 1800) / (1880 - 1800) * (total_since_1880_m * 0.2)

@st.cache
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
# 국가별 피해 요약
# -----------------------
IMPACT_SUMMARIES = {
    "Tuvalu": "투발루는 해발 약 2~3m로 해수면 상승의 직접적 위협을 받습니다. 경작지·식수 오염, 거주지 침수, 환경 난민 발생 위험이 있습니다.",
    "Bangladesh": "방글라데시의 저지대 농경지는 홍수와 염수 침입으로 피해를 입습니다. 인구 밀집 지역 침수·토지 소실로 인한 식량 안전 문제가 심각합니다.",
    "Maldives": "몰디브는 섬의 상실 위험이 큽니다. 해안 침식과 담수 오염 사례가 있습니다.",
    "Netherlands": "네덜란드는 방조제와 수문으로 해수 침입을 막고 있으나, 지속적 관리와 추가 투자가 필요합니다.",
    "Italy": "베네치아는 해수면 상승과 홍수('아쿠아 알타')로 역사적 도시 피해가 발생합니다.",
    "United States": "뉴올리언스 등 일부 미국 연안 도시는 해안 침식과 장기적 해수면 상승에 위협받습니다.",
}
GENERIC_IMPACT = "이 지역은 해수면 상승으로 해안 침식, 토지 소실, 염수 침입 등의 영향을 받을 수 있습니다."

# -----------------------
# 원형 폴리곤 생성
# -----------------------
def circle_polygon(lat, lon, radius_m, n_points=64):
    lat_deg_per_m = 1.0 / 111320.0
    lon_deg_per_m = 1.0 / (111320.0 * cos(lat * pi / 180.0))
    angles = np.linspace(0, 2 * pi, n_points)
    coords = []
    for a in angles:
        dlat = (radius_m * sin(a)) * lat_deg_per_m
        dlon = (radius_m * cos(a)) * lon_deg_per_m
        coords.append([lon + dlon, lat + dlat])
    return {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [coords]}}

# -----------------------
# 사용자 입력
# -----------------------
col1, col2 = st.columns([2,1])
with col1:
    place_input = st.text_input("🔎 장소 입력 (예: 투발루, 베네치아, 다카)")
with col2:
    year_input = st.number_input("◀ 과거 연도 선택 (1800~2024)", min_value=1800, max_value=2024, value=1900, step=1)

# -----------------------
# 비교 버튼
# -----------------------
if st.button("비교 및 지도 표시"):
    if not place_input.strip():
        st.error("먼저 장소 이름을 입력해주세요.")
    else:
        lat, lon, display = geocode_city(place_input)
        if lat is None:
            st.error("해당 장소를 찾을 수 없습니다.")
        else:
            # 전지구 평균
            past_sl = get_global_sea_level_rise_m(year_input)
            now_sl = get_global_sea_level_rise_m(2025)
            diff_sl = now_sl - past_sl

            past_temp = get_global_temperature_anomaly_c(year_input)
            now_temp = get_global_temperature_anomaly_c(2025)
            diff_temp = now_temp - past_temp

            country = display.split(",")[-1].strip() if "," in display else display
            impact_text = IMPACT_SUMMARIES.get(country, GENERIC_IMPACT)

            # 텍스트 출력
            st.subheader(f"🗺️ 검색 결과: {display}")
            st.markdown(f"- **선택 연도:** {year_input}  |  **기준:** 2025")
            st.markdown(f"- **{year_input} 해수면 상승 근사:** {past_sl:.3f} m")
            st.markdown(f"- **2025 해수면 상승 근사:** {now_sl:.3f} m")
            st.markdown(f"- **두 시점 차이:** {diff_sl:.3f} m")
            st.markdown(f"- **{year_input} 온도 이상치 근사:** {past_temp:.2f} °C")
            st.markdown(f"- **2025 온도 이상치 근사:** {now_temp:.2f} °C")
            st.markdown(f"- **두 시점 온도 차이:** {diff_temp:.2f} °C")
            st.info(impact_text)

            # -----------------------
            # 지도 표시
            # -----------------------
            scale_factor = 5000
            radius_now  = max(200, now_sl*scale_factor)
            radius_diff = max(200, diff_sl*scale_factor)

            poly_now  = circle_polygon(lat, lon, radius_now)
            poly_diff = circle_polygon(lat, lon, radius_diff)

            geo_now  = {"type":"FeatureCollection","features":[poly_now]}
            geo_diff = {"type":"FeatureCollection","features":[poly_diff]}

            view = pdk.ViewState(latitude=lat, longitude=lon, zoom=7, pitch=30)
            left_col, right_col = st.columns(2)

            # 왼쪽: 2025 기준 — 빨강
            with left_col:
                st.markdown("### 2025 기준 — 침수 예상 영역 (빨강)")
                layer_now = pdk.Layer(
                    "GeoJsonLayer", geo_now,
                    stroked=True, filled=True,
                    get_fill_color=[255,100,100,120],
                    get_line_color=[180,0,0],
                    pickable=True
                )
                arrow_layer = pdk.Layer(
                    "IconLayer",
                    data=pd.DataFrame([{"lat":lat,"lon":lon}]),
                    get_icon='{"url":"https://img.icons8.com/ios-filled/50/000000/up-right-arrow.png","width":50,"height":50,"anchorY":50}',
                    get_size=4,
                    get_position='[lon,lat]'
                )
                st.pydeck_chart(pdk.Deck(layers=[layer_now, arrow_layer], initial_view_state=view, map_style="light"))

            # 오른쪽: 선택 연도 + 2025 대비 차이 — 빨강 오버레이만
            with right_col:
                st.markdown(f"### {year_input} 기준 + 2025 대비 증가분")
                layer_diff = pdk.Layer(
                    "GeoJsonLayer", geo_diff,
                    stroked=False, filled=True,
                    get
