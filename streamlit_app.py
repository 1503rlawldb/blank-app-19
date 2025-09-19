# app.py
import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests
from math import cos, sin, pi

# -----------------------
# 설정
# -----------------------
st.set_page_config(page_title="물러서는 땅, 다가오는 바다 — 비교 시뮬레이터", layout="wide")
st.title("🌊 물러서는 땅, 다가오는 바다 — 연도별 해수면 비교 & 시각화")

# -----------------------
# 유틸리티: 지오코딩 (Nominatim)
# -----------------------
def geocode_city(city_name):
    """
    Nominatim(OpenStreetMap)으로 장소 검색 -> (lat, lon, display_name)
    """
    url = f"https://nominatim.openstreetmap.org/search"
    params = {"q": city_name, "format": "json", "limit": 1}
    headers = {"User-Agent": "sea-level-app/1.0 (+https://example.com)"}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    if resp.status_code == 200 and len(resp.json()) > 0:
        item = resp.json()[0]
        return float(item["lat"]), float(item["lon"]), item["display_name"]
    return None, None, None

# -----------------------
# 간단 모델: 전지구 평균 해수면 변화 & 기온 이상치 (교육용 근사)
# -----------------------
@st.cache_data
def get_global_sea_level_rise_m(year):
    """
    교육용 근사: 연도별 전지구 평균 해수면 상승(m). (1880 이후 관측 기반 근사)
    - 현재(2025) 기준 전체 상승을 약 0.25 m(25 cm)로 가정 (교육용)
    - 1800~1880 구간은 보간/추정으로 처리
    """
    now = 2025
    total_since_1880_m = 0.25  # 1880~2025 전체 상승 약 0.25m (예시)
    if year >= 1880:
        frac = (year - 1880) / (now - 1880)
        return frac * total_since_1880_m
    else:
        # 1800~1880: 작은 상승분을 선형 보간으로 가정 (교육용)
        return (year - 1800) / (1880 - 1800) * (total_since_1880_m * 0.2)

@st.cache_data
def get_global_temperature_anomaly_c(year):
    """
    교육용 근사: pre-industrial(약 1850-1900) 대비 온도 이상치 (°C)
    - 현재(2025) 약 +1.5°C로 가정
    """
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
# 간단한 '국가별 피해 요약' 데이터 (자주 묻는 사례들)
# -----------------------
IMPACT_SUMMARIES = {
    "Tuvalu": (
        "투발루(Tuvalu)는 평균 해발고도 약 2~3m로 해수면 상승의 직접적 위협을 받습니다. "
        "바닷물 유입으로 경작지·식수 오염, 거주지 침수 사례가 보고되었으며, 중장기적으로는 이주(환경 난민) 문제가 심화되고 있습니다."
    ),
    "Bangladesh": (
        "방글라데시의 저지대 농경지는 홍수와 염수 침입으로 피해를 입고 있습니다. "
        "인구 밀집 지역의 침수·토지 소실로 인한 이주·식량 안전 문제가 심각합니다."
    ),
    "Maldives": (
        "몰디브는 평균 해발고도가 매우 낮아, 섬의 상실 위험이 큽니다. 많은 섬이 해안 침식과 담수 오염을 겪고 있습니다."
    ),
    "Netherlands": (
        "네덜란드는 수세기 동안 방조제와 수문 등으로 해수 침입을 막아왔습니다. "
        "지속적 관리와 추가적 인프라 투자가 필요한 상황이며, 일부 지역은 지반 침하도 문제입니다."
    ),
    "Italy": (
        "베네치아(이탈리아)는 해수면 상승과 연안 침식, 그리고 '아쿠아 알타'(홍수) 현상으로 역사적 도시 피해를 입고 있습니다."
    ),
    "United States": (
        "뉴올리언스 등 일부 미국 연안 도시는 허리케인·홍수 취약성과 더불어 장기적인 해안 침식과 해수면 상승으로 위협받습니다."
    ),
}
# 범용(해당 국가 정보가 없을 때)
GENERIC_IMPACT = (
    "이 지역은 해수면 상승으로 해안 침식, 토지 소실, 염수 침입(담수 오염), 폭풍 해일 시 피해 증가 등의 영향을 받을 수 있습니다. "
    "정확한 영향은 지역의 해발고도, 방조·제방 인프라, 지반침하 여부, 조석 특성 등에 따라 달라집니다."
)

# -----------------------
# 원형 폴리곤 생성 (위도/경도, 반경(m) -> GeoJSON 폴리곤)
# -----------------------
def circle_polygon(lat, lon, radius_m, n_points=64):
    """
    중심(lat, lon)으로 radius(m)인 원형 다각형을 근사(단위: meter)
    단위 변환: 위도 1 deg ~ 111320 m, 경도 1 deg ~ 111320*cos(lat)
    """
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
# 사용자 입력 UI
# -----------------------
col1, col2 = st.columns([2, 1])
with col1:
    place_input = st.text_input("🔎 비교할 장소(도시/국가/장소)를 입력하세요 (예: Tuvalu, Incheon, Venice, Dhaka)", "")
with col2:
    year_input = st.number_input("◀ 비교할 과거 연도 선택 (1800 ~ 2024)", min_value=1800, max_value=2024, value=1900, step=1)

# 비교 버튼
if st.button("비교 및 지도 표시"):
    if not place_input.strip():
        st.error("먼저 장소 이름을 입력해주세요.")
    else:
        lat, lon, display = geocode_city(place_input)
        if lat is None:
            st.error("해당 장소를 찾을 수 없습니다. 영어/한글 이름을 확인해 주세요.")
        else:
            # 기본 수치(전지구 평균 기반)
            past_sl_m = get_global_sea_level_rise_m(year_input)
            now_sl_m = get_global_sea_level_rise_m(2025)
            diff_m = now_sl_m - past_sl_m

            past_temp = get_global_temperature_anomaly_c(year_input)
            now_temp = get_global_temperature_anomaly_c(2025)
            temp_diff = now_temp - past_temp

            # 국가/영역 이름 추출 (display에 country 포함)
            country = display.split(",")[-1].strip() if "," in display else display

            # 피해 설명 가져오기 (사례가 없으면 일반 설명)
            impact_text = IMPACT_SUMMARIES.get(country, None)
            if impact_text is None:
                # 일부 표준화된 이름 매핑 (예: Tuvalu는 display에 'Tuvalu'로 됨)
                for k in IMPACT_SUMMARIES.keys():
                    if k.lower() in display.lower():
                        impact_text = IMPACT_SUMMARIES[k]
                        break
            if impact_text is None:
                impact_text = GENERIC_IMPACT

            # 화면에 텍스트 출력 (요약 + 수치)
            st.subheader(f"🗺️ 검색 결과: {display}")
            st.markdown(f"- **선택 연도:** {year_input}  |  **비교 기준(앱 기준):** 2025")
            st.markdown(f"- **{year_input} 전지구 평균 해수면 상승(근사):** {past_sl_m:.3f} m")
            st.markdown(f"- **2025 전지구 평균 해수면 상승(근사):** {now_sl_m:.3f} m")
            st.markdown(f"- **두 시점 해수면 차이(전지구 근사):** {diff_m:.3f} m")
            st.markdown(f"- **{year_input} 전지구 평균 기온 이상치(근사):** {past_temp:.2f} °C")
            st.markdown(f"- **2025 전지구 평균 기온 이상치(근사):** {now_temp:.2f} °C")
            st.markdown(f"- **두 시점 기온 차이(전지구 근사):** {temp_diff:.2f} °C")

            st.markdown("**해당 국가·지역에서 관측되거나 보고된 영향(요약):**")
            st.info(impact_text)

            # 출처: (요구대로 '모든 설명 아래'에 출처를 표기)
            DATA_SOURCES_MD = """
**데이터 및 참고 출처 (교육/시연용)**
- Our World in Data — Global mean sea level summaries and charts (관측/정리 자료 기반).  
- NASA Climate — Global temperature (vital signs).  
- European Environment Agency (EEA) — Sea level analyses.  
- OpenStreetMap / Nominatim — 위치(지오코딩) 검색 API.  
(참고: 실제 연구/정밀 모델링에는 NOAA, IPCC 보고서, 국가별 관측소(조위 관측소), SRTM/DEM 전지구 표고 데이터 사용 권장)
"""
            st.markdown(DATA_SOURCES_MD)

            # -----------------------
            # 지도 시각화: 2025 vs 선택 연도 (두 개의 지도를 좌우로 표시)
            # - 간단한 근사 침수 폴리곤 생성: (전지구 평균 해수면 상승 값을 반영한 '반경' 근사)
            # -----------------------
            # 반경 계산 (근사): m 단위. 시각화를 위해 확장계수 사용.
            # 설명: 실제 침수는 해안선 따라 일어나므로 '원형 확대'는 단순 시각화 보조 수단입니다.
            # (scale_factor는 시각적 가시성 조절용)
            scale_factor = 5000  # 1 m 해수면 차이 -> scale_factor * m (시각화 반경, meters). 값 조절 가능.
            radius_past_m = max(200, past_sl_m * scale_factor)    # 최소 반경 보장
            radius_now_m  = max(200, now_sl_m  * scale_factor)
            radius_diff_m = max(200, diff_m * scale_factor)

            # 폴리곤 생성
            poly_past = circle_polygon(lat, lon, radius_past_m)
            poly_now  = circle_polygon(lat, lon, radius_now_m)
            poly_diff = circle_polygon(lat, lon, radius_diff_m)

            # GeoJSON 데이터 프레임 생성 (pydeck에 쓸 형식)
            geo_past = {"type": "FeatureCollection", "features": [poly_past]}
            geo_now  = {"type": "FeatureCollection", "features": [poly_now]}
            geo_diff = {"type": "FeatureCollection", "features": [poly_diff]}

            # 사이드-바이-사이드 지도
            left_col, right_col = st.columns(2)

            # 공통 view_state
            view = pdk.ViewState(latitude=lat, longitude=lon, zoom=7, pitch=30)

            # 왼쪽: 2025 (현재) -> 빨간색(심한 침수 시각화)
            with left_col:
                st.markdown("### 2025 기준(근사) — 침수 예상 영역 (빨간색)")
                layer_now = pdk.Layer(
                    "GeoJsonLayer",
                    geo_now,
                    stroked=True,
                    filled=True,
                    get_fill_color="[255, 60, 60, 120]",   # 반투명 빨강
                    get_line_color=[180, 0, 0],
                    pickable=True
                )
                point_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"lat": lat, "lon": lon}]),
                    get_position='[lon, lat]',
                    get_radius=20000,
                    get_fill_color=[0, 114, 178]
                )
                deck_now = pdk.Deck(layers=[layer_now, point_layer], initial_view_state=view, map_style="light")
                st.pydeck_chart(deck_now)

            # 오른쪽: 선택 연도 -> 파란색(과거) + 차이 영역 (빨강 오버레이로 비교)
            with right_col:
                st.markdown(f"### {year_input} 기준(근사) — 침수 예상 영역 (파란색) + 2025와의 차이(빨간 오버레이)")
                layer_past = pdk.Layer(
                    "GeoJsonLayer",
                    geo_past,
                    stroked=True,
                    filled=True,
                    get_fill_color="[60, 120, 255, 100]",  # 반투명 파랑
                    get_line_color=[0, 60, 180],
                    pickable=True
                )
                layer_diff = pdk.Layer(
                    "GeoJsonLayer",
                    geo_diff,
                    stroked=False,
                    filled=True,
                    get_fill_color="[255, 60, 60, 80]"  # 차이(증가분) 반투명 빨강
                )
                point_layer2 = pdk.Layer(
                    "ScatterplotLayer",
                    data=pd.DataFrame([{"lat": lat, "lon": lon}]),
                    get_position='[lon, lat]',
                    get_radius=20000,
                    get_fill_color=[0, 114, 178]
                )
                deck_past = pdk.Deck(layers=[layer_past, layer_diff, point_layer2], initial_view_state=view, map_style="light")
                st.pydeck_chart(deck_past)

            # 하단: 설명 및 추가 권고
            st.markdown("---")
            st.subheader("💡 해설 및 권고 (요약)")
            st.write(
                "• 위 지도는 **전지구 평균 해수면 상승 근사치**에 기반한 '시각적 비교'입니다. "
                "실제 침수는 해안선 형태, 조석, 국지적 해수면 변화, 방조/제방 시설, 지반 침하 등 여러 요인에 좌우됩니다.\n\n"
                "• 보다 정확한 지역별 침수 분석을 위해서는 고해상도 DEM (예: LiDAR 기반 표고), "
                "국가 조위 관측소 데이터, 지역 해양·기후 모델을 연동해야 합니다.\n\n"
                "• 교육적·정책적 목적이라면 (1) 온실가스 감축(재생에너지 확대), (2) 자연기반 해안보호(갯벌·맹그로브 복원), "
                "(3) 인프라(방조제·제방) 개선 및 장기적 이주·도시계획 수립을 권장합니다."
            )

            st.markdown("---")
            st.markdown("**데이터 및 참고 출처 (앱 설명/지도/수치 근사에 사용된 참조)**")
            st.markdown("""
- Our World in Data: sea level summaries (교육적 근사치 참고).  
- NASA Climate: global temperature indicators (교육적 근사치 참고).  
- European Environment Agency (EEA) 자료(해수면 변화 관련).  
- OpenStreetMap / Nominatim: 위치(지오코딩) 검색.  
- (정밀 연구 시 참고) NOAA tide gauge, IPCC 보고서, SRTM/DEM, LiDAR 고도 데이터.
""")
