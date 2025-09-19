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
# 지오코딩 (Nominatim 안전 처리)
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
    except Exception as e:
        st.error(f"지오코딩 실패: {e}")
    return None, None, None

# -----------------------
# 교육용 근사: 전지구 평균 해수면 상승/온도 이상치
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
    "Tuvalu": "투발루(Tuvalu)는 평균 해발고도 약 2~3m로 해수면 상승의 직접적 위협을 받습니다. 바닷물 유입으로 경작지·식수 오염, 거주지 침수 사례가 보고되었으며, 중장기적으로는 이주 문제가 심화됩니다.",
    "Bangladesh": "방글라데시의 저지대 농경지는 홍수와 염수 침입으로 피해를 입고 있습니다. 인구 밀집 지역의 침수·토지 소실로 인한 이주·식량 안전 문제가 심각합니다.",
    "Maldives": "몰디브는 평균 해발고도가 매우 낮아, 섬의 상실 위험이 큽니다. 많은 섬이 해안 침식과 담수 오염을 겪고 있습니다.",
    "Netherlands": "네덜란드는 수세기 동안 방조제와 수문 등으로 해수 침입을 막아왔습니다. 지속적 관리와 추가적 인프라 투자가 필요한 상황이며, 일부 지역은 지반 침하도 문제입니다.",
    "Italy": "베네치아(이탈리아)는 해수면 상승과 연안 침식, '아쿠아 알타'(홍수) 현상으로 역사적 도시 피해를 입고 있습니다.",
    "United States": "뉴올리언스 등 일부 미국 연안 도시는 허리케인·홍수 취약성과 장기적 해안 침식 및 해수면 상승으로 위협받습니다.",
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
    place_input = st.text_input("🔎 장소 입력 (예: Tuvalu, Venice, Dhaka)")
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
            radius_past = max(200, past_sl*scale_factor)
            radius_now  = max(200, now_sl*scale_factor)
            radius_diff = max(200, diff_sl*scale_factor)

            poly_past = circle_polygon(lat, lon, radius_past)
            poly_now  = circle_polygon(lat, lon, radius_now)
            poly_diff = circle_polygon(lat, lon, radius_diff)

            geo_past = {"type":"FeatureCollection","features":[poly_past]}
            geo_now  = {"type":"FeatureCollection","features":[poly_now]}
            geo_diff = {"type":"FeatureCollection","features":[poly_diff]}

            view = pdk.ViewState(latitude=lat, longitude=lon, zoom=7, pitch=30)
            left_col, right_col = st.columns(2)

            # 왼쪽: 2025
            with left_col:
                st.markdown("### 2025 기준 — 침수 예상 영역 (빨강)")
                layer_now = pdk.Layer(
                    "GeoJsonLayer", geo_now,
                    stroked=True, filled=True,
                    get_fill_color=[255,60,60,120],
                    get_line_color=[180,0,0],
                    pickable=True
                )
                point_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"lat":lat,"lon":lon}]),
                    get_position='[lon,lat]',
                    get_radius=20000,
                    get_fill_color=[0,114,178]
                )
                st.pydeck_chart(pdk.Deck(layers=[layer_now, point_layer], initial_view_state=view, map_style="light"))

            # 오른쪽: 과거 + 차이
            with right_col:
                st.markdown(f"### {year_input} 기준 + 2025 대비 증가분")
                layer_past = pdk.Layer(
                    "GeoJsonLayer", geo_past,
                    stroked=True, filled=True,
                    get_fill_color=[60,120,255,100],
                    get_line_color=[0,60,180],
                    pickable=True
                )
                layer_diff = pdk.Layer(
                    "GeoJsonLayer", geo_diff,
                    stroked=False, filled=True,
                    get_fill_color=[255,60,60,80]
                )
                point_layer2 = pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"lat":lat,"lon":lon}]),
                    get_position='[lon,lat]',
                    get_radius=20000,
                    get_fill_color=[0,114,178]
                )
                st.pydeck_chart(pdk.Deck(layers=[layer_past, layer_diff, point_layer2], initial_view_state=view, map_style="light"))

            st.markdown("---")
            st.subheader("💡 교육용 해설 및 권고")
            st.write(
                "• 위 지도는 **전지구 평균 해수면 상승 근사치** 기반 시각화입니다.\n"
                "• 실제 침수는 해안선, 조석, 방조·제방, 지반침하 등 다양한 요인에 좌우됩니다.\n"
                "• 정책적 권고: 온실가스 감축, 자연기반 해안보호, 인프라 개선, 장기적 도시계획 및 이주 고려"
            )
            st.markdown("---")
            st.markdown("""
**참고 데이터 출처**
- Our World in Data (교육적 근사치)
- NASA Climate (교육적 근사치)
- European Environment Agency (EEA)
- OpenStreetMap / Nominatim
- 정밀 연구 시 NOAA, IPCC, SRTM/DEM, LiDAR 활용
""")
