import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature

# --------------------------
# 국가별 피해 사례 및 대처 방안 데이터
# --------------------------
country_info = {
    "투발루": {
        "피해": "평균 해발 2~3m로 해수면 상승에 가장 취약. 농경지와 식수원 침수, 환경 난민 발생.",
        "대처": "국제 사회에 이민 요청, 기후변화 협약에서 생존권 보장을 요구."
    },
    "방글라데시": {
        "피해": "매년 우기마다 농경지가 침수되어 수백만 명의 주민 생계 위협.",
        "대처": "홍수 방지 제방 건설, 기후 난민 이주 정책 논의."
    },
    "몰디브": {
        "피해": "일부 섬이 바닷물에 잠겨 거주 불가능 지역 증가.",
        "대처": "관광 수익으로 해안 방어 시설 건설, 산호초 복원 프로젝트."
    },
    "네덜란드": {
        "피해": "저지대 국가 특성상 해수면 상승에 직접적인 위협.",
        "대처": "세계 최고 수준의 방조제와 수문 시스템 운영."
    },
    "미국 마이애미": {
        "피해": "‘Sunny Day Flooding’ 현상으로 도로가 주기적으로 침수.",
        "대처": "해안 방어벽 설치, 빗물 배수 시스템 강화."
    },
    "인도네시아 자카르타": {
        "피해": "해수면 상승과 지반 침하로 도심 침수 심각. 수도 이전 논의.",
        "대처": "수도 이전(누산타라 건설), 대규모 해안 방조제 건설."
    }
}

# --------------------------
# Streamlit UI
# --------------------------
st.title("🌊 해수면 상승 피해 국가 검색 및 역사 비교 대시보드")

# 검색창
country = st.text_input("국가명을 입력하세요 (예: 투발루, 방글라데시, 몰디브, 네덜란드, 미국 마이애미, 인도네시아 자카르타)")

if country in country_info:
    st.subheader(f"📍 {country}의 해수면 상승 피해 사례와 대처 방안")
    st.markdown(f"**피해 사례:** {country_info[country]['피해']}")
    st.markdown(f"**대처 방안:** {country_info[country]['대처']}")
elif country:
    st.warning("❌ 해당 국가 데이터가 없습니다. 다른 국가를 입력해 보세요.")

# --------------------------
# 과거 vs 현재 해수면 지도
# --------------------------
st.subheader("🌍 1800년 vs 현재 해수면 비교 지도 (시뮬레이션)")

# 지도 크기 설정
fig = plt.figure(figsize=(12,6))
ax = plt.axes(projection=ccrs.Robinson())
ax.set_global()
ax.coastlines()
ax.add_feature(cfeature.LAND, facecolor='lightgray')
ax.add_feature(cfeature.OCEAN, facecolor='lightblue')

# 해수면 상승 차이 시뮬레이션 (1800년=0, 현재=1~5m 랜덤 예시)
height, width = 180, 360  # 단순 예시용
sea_level_diff = np.random.uniform(0, 5, (height, width))  # m 단위
# 색상 맵: 0-1m 초록, 1-3m 노랑, 3-5m 빨강
from matplotlib.colors import ListedColormap, BoundaryNorm

cmap = ListedColormap(['#00ff00','#ffcc00','#ff3300'])
bounds = [0,1,3,5]
norm = BoundaryNorm(bounds, cmap.N)

# 간단한 이미지로 지도 위에 overlay
extent = [-180,180,-90,90]
ax.imshow(sea_level_diff, origin='upper', extent=extent, transform=ccrs.PlateCarree(), cmap=cmap, norm=norm, alpha=0.6)

# 범례 추가
import matplotlib.patches as mpatches
green_patch = mpatches.Patch(color='#00ff00', label='0-1m (안정)')
yellow_patch = mpatches.Patch(color='#ffcc00', label='1-3m (조심)')
red_patch = mpatches.Patch(color='#ff3300', label='3-5m (위험)')
plt.legend(handles=[green_patch, yellow_patch, red_patch], loc='lower left')

st.pyplot(fig)

# --------------------------
# 데이터 출처
# --------------------------
st.markdown("""--- 
📌 **데이터 출처**  
- IPCC (2021) "Sixth Assessment Report"  
- NASA Sea Level Change Team  
- NOAA (National Oceanic and Atmospheric Administration)  
""")
