import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import requests

st.set_page_config(page_title="물러서는 땅, 다가오는 바다", layout="wide")

st.title("🌍 해수면 상승 시뮬레이션 대시보드")

# --- 도시 검색 (전 세계) ---
search_term = st.text_input("도시 이름을 검색하세요 (예: Incheon, Busan, Tuvalu, New York, Tokyo)", "")

def geocode_city(city_name):
    """도시 이름을 위도/경도로 변환 (Nominatim API 사용)"""
    url = f"https://nominatim.openstreetmap.org/search?format=json&q={city_name}"
    resp = requests.get(url, headers={"User-Agent": "streamlit-app"})
    if resp.status_code == 200 and len(resp.json()) > 0:
        loc = resp.json()[0]
        return float(loc["lat"]), float(loc["lon"]), loc["display_name"]
    return None, None, None

if search_term.strip():
    lat, lon, full_name = geocode_city(search_term)
    if lat and lon:
        st.success(f"🔎 '{full_name}' 위치를 찾았습니다.")

        # 슬라이더로 해수면 상승 높이 설정
        sea_rise_m = st.slider("가상 해수면 상승 높이 (m)", 0.0, 10.0, 1.0, step=0.1)

        # 평균 해발고도는 외부 데이터가 필요하지만, 여기선 임시 랜덤 값 예시
        elev_m = np.random.uniform(0, 5)  
        inundated = elev_m <= sea_rise_m

        df_location = pd.DataFrame([{
            "lat": lat, "lon": lon, "elev_m": elev_m,
            "inundated": inundated, "place": full_name,
            "color": [220, 20, 60] if inundated else [0, 114, 178]
        }])

        # pydeck 지도 시각화
        view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=9, pitch=45)
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_location,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=8000,
            pickable=True
        )
        tooltip = {
            "html": "<b>{place}</b><br/>평균 해발고도: {elev_m} m<br/>침수 위험: {inundated}",
            "style": {"backgroundColor": "black", "color": "white"}
        }

        r = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style="light"  # ✅ Mapbox 토큰 없이도 표시됨
        )

        st.pydeck_chart(r)
        st.caption(f"'{full_name}'의 평균 해발고도는 {elev_m:.1f}m (임시값) 입니다. 해수면이 이보다 높아지면 붉은 점으로 표시됩니다.")
    else:
        st.error(f"'{search_term}' 위치를 찾을 수 없습니다. 영어/한글로 다시 입력해보세요.")
else:
    st.info("도시를 검색하면 지도에서 위치와 해수면 시뮬레이션이 나타납니다.")
