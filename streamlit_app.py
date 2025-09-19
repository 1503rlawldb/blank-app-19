import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests
from io import StringIO

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="물러서는 땅, 다가오는 바다",
    page_icon="🌊",
    layout="wide"
)

# --- 지도 표시 함수 ---
def plot_map(lat, lon, elev_m, sea_rise_m, zoom=8, title=""):
    # 현재 해수면과 비교
    inundated = elev_m <= sea_rise_m

    # 지도 시뮬레이션용 데이터프레임
    df_location = pd.DataFrame([{
        "lat": lat,
        "lon": lon,
        "elev_m": elev_m,
        "inundated": inundated,
        "color": [220, 20, 60, 120] if inundated else [0, 114, 178, 80]  # 빨강/파랑 투명도
    }])

    # 뷰 세팅
    view_state = pdk.ViewState(
        latitude=lat,
        longitude=lon,
        zoom=zoom,
        bearing=0,
        pitch=45
    )

    # ScatterplotLayer 삭제 -> 동그라미 제거
    # PolygonLayer나 ColumnLayer를 써야 더 현실적인 침수범위 표현 가능
    layer = pdk.Layer(
        "ColumnLayer",
        data=df_location,
        get_position='[lon, lat]',
        get_elevation='elev_m',
        elevation_scale=500,
        radius=20000,
        get_fill_color='color',
        pickable=True,
        extruded=True
    )

    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"html": f"<b>{title}</b><br/>해발: {elev_m}m<br/>침수 위험: {inundated}"}
    )
    return r


# --- 검색 기능 ---
LOCATIONS = {
    "투발루": {"lat": -8.5240, "lon": 179.1942, "elev_m": 1.5, "zoom": 11},
    "인천": {"lat": 37.4563, "lon": 126.7052, "elev_m": 3.5, "zoom": 10},
    "부산": {"lat": 35.1796, "lon": 129.0756, "elev_m": 2.8, "zoom": 10},
    "암스테르담": {"lat": 52.3702, "lon": 4.8952, "elev_m": -2.0, "zoom": 10}
}

st.title("🌊 해수면 상승 지도 시뮬레이션")

search_term = st.text_input("도시 이름을 입력하세요 (예: 투발루, 인천, 부산, 암스테르담)", "")
if search_term.strip() and search_term in LOCATIONS:
    location_data = LOCATIONS[search_term]

    st.subheader(f"'{search_term}' 지역 시뮬레이션")
    sea_rise_m = st.slider("가상 해수면 상승 높이 (m)", 0.0, 5.0, 1.0, step=0.1)

    # 2025년 현재 지도
    st.markdown("#### 2025년 해수면 시뮬레이션")
    r_current = plot_map(
        location_data["lat"], location_data["lon"], location_data["elev_m"],
        sea_rise_m, location_data["zoom"], title=f"{search_term} (2025)"
    )
    st.pydeck_chart(r_current)

    # 과거 지도 (예시: 1900년)
    st.markdown("#### 과거와 비교 (1900년)")
    r_past = plot_map(
        location_data["lat"], location_data["lon"], location_data["elev_m"],
        0.0, location_data["zoom"], title=f"{search_term} (1900)"
    )
    st.pydeck_chart(r_past)

    st.caption(f"빨간색 = 침수 위험 지역 / 파란색 = 안전 지역")

else:
    st.info("검색 가능한 도시를 입력하세요. (예: 투발루, 인천, 부산, 암스테르담)")


# --- 출처 ---
st.divider()
st.markdown("""
**데이터 출처**
- [NASA Climate Change Data](https://climate.nasa.gov/)
- [NOAA Sea Level Rise Data](https://www.climate.gov/)
- [IPCC 6차 보고서](https://www.ipcc.ch/ar6/)
- [Our World in Data](https://ourworldindata.org/co2-and-greenhouse-gas-emissions)
""")
