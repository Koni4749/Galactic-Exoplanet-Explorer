import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import urllib.parse
import time

# 1. 페이지 설정
st.set_page_config(
    page_title="NASA Galactic Explorer",
    page_icon="🔭",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🔭 NASA 실측 외계 행성 탐색기 (Real Exoplanet Data)")
st.markdown("### 인류가 현재까지 발견한 **진짜 외계 행성들**을 3D 지도로 탐험하세요. 🚀")
st.markdown("---")

# 2. NASA API 데이터 로딩 (캐싱을 통해 매번 다운로드하지 않도록 최적화)
@st.cache_data(ttl=86400) # 하루에 한 번만 새로고침
def load_nasa_data():
    # NASA Exoplanet Archive TAP API 쿼리 (필요한 데이터만 SQL처럼 요청)
    query = "select pl_name, sy_dist, pl_masse, pl_eqt, ra, dec from ps where default_flag=1 and sy_dist is not null"
    url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={urllib.parse.quote(query)}&format=csv"
    
    df = pd.read_csv(url)
    
    # 3. 데이터 전처리 및 단위 변환
    # 파섹(parsec)을 광년(Light Years)으로 변환
    df['Distance (LY)'] = df['sy_dist'] * 3.26156 
    # 켈빈(K) 온도를 섭씨(°C)로 변환
    df['Temperature (°C)'] = df['pl_eqt'] - 273.15 
    
    # 우주 관측 데이터 특성상 결측치(NaN)가 많으므로 중간값으로 채움
    df['Mass (Earths)'] = df['pl_masse'].fillna(df['pl_masse'].median())
    df['Temperature (°C)'] = df['Temperature (°C)'].fillna(df['Temperature (°C)'].median())
    
    # 4. 천구 좌표계(적경 RA, 적위 DEC)를 3D 직교 좌표계(X, Y, Z)로 변환 (지구를 중심(0,0,0)으로 둠)
    ra_rad = np.radians(df['ra'])
    dec_rad = np.radians(df['dec'])
    dist = df['Distance (LY)']
    
    df['X'] = dist * np.cos(dec_rad) * np.cos(ra_rad)
    df['Y'] = dist * np.cos(dec_rad) * np.sin(ra_rad)
    df['Z'] = dist * np.sin(dec_rad)
    
    # 5. 거주 가능 지수 계산 (지구 환경 기준: 15°C, 질량 1)
    temp_score = np.abs(df['Temperature (°C)'] - 15) * 0.3
    mass_score = np.abs(df['Mass (Earths)'] - 1) * 2
    df['Habitability Score'] = 100 - temp_score - mass_score
    df['Habitability Score'] = df['Habitability Score'].clip(lower=0, upper=100)
    
    df.rename(columns={'pl_name': 'Planet Name'}, inplace=True)
    return df

with st.spinner("NASA 데이터베이스에 접속 중... 실제 우주망원경 데이터를 수신하고 있습니다... 📡"):
    raw_df = load_nasa_data()

# 6. 사이드바 컨트롤러 (지구로부터의 거리 필터)
st.sidebar.header("📡 심우주 필터링")
max_distance = st.sidebar.slider(
    "탐색할 최대 거리 (광년)", 
    min_value=10, 
    max_value=int(raw_df['Distance (LY)'].max()), 
    value=3000, 
    step=50
)

# 필터링 적용
df = raw_df[raw_df['Distance (LY)'] <= max_distance]

# 7. 핵심 지표 (Metrics)
st.subheader("📊 NASA 관측 데이터 브리핑")
col1, col2, col3, col4 = st.columns(4)

high_habitable = len(df[df["Habitability Score"] > 80])
closest_planet = df.loc[df['Distance (LY)'].idxmin()]

col1.metric("발견된 행성 수 (필터링 됨)", f"{len(df):,} 개")
col2.metric("가장 가까운 행성", f"{closest_planet['Planet Name']}")
col3.metric("최소 거리", f"{closest_planet['Distance (LY)']:.2f} 광년")
col4.metric("지구와 유사한 행성 후보", f"{high_habitable} 개")

st.markdown("---")

# 8. 메인 시각화: 3D 우주 지도
st.subheader(f"🌐 3D 은하 성도 (반경 {max_distance:,} 광년 이내)")
st.markdown("중앙(0,0,0)이 바로 우리가 있는 **지구(태양계)**입니다! 마우스로 우주를 회전시켜보세요.")

fig = px.scatter_3d(
    df, x='X', y='Y', z='Z',
    color='Habitability Score',
    size='Mass (Earths)',
    hover_name='Planet Name',
    hover_data=['Distance (LY)', 'Temperature (°C)', 'Mass (Earths)'],
    color_continuous_scale=px.colors.sequential.Plasma,
    opacity=0.8,
    size_max=20
)

fig.update_layout(
    scene=dict(
        xaxis=dict(showbackground=False, showticklabels=False, title=''),
        yaxis=dict(showbackground=False, showticklabels=False, title=''),
        zaxis=dict(showbackground=False, showticklabels=False, title='')
    ),
    paper_bgcolor='black',
    plot_bgcolor='black',
    margin=dict(l=0, r=0, b=0, t=30)
)

st.plotly_chart(fig, use_container_width=True)

# 9. 데이터 테이블
st.subheader("📋 실측 데이터 테이블 (거주 가능성 높은 순)")
st.dataframe(
    df[['Planet Name', 'Distance (LY)', 'Mass (Earths)', 'Temperature (°C)', 'Habitability Score']]
    .sort_values(by="Habitability Score", ascending=False)
    .head(100), 
    use_container_width=True
)

st.caption("※ 데이터 출처: NASA Exoplanet Archive (API 연동). 결측치는 통계적 중간값으로 대체되었습니다.")
