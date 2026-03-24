import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import urllib.parse
import time

# 1. 페이지 설정
st.set_page_config(page_title="NASA Command Center", page_icon="🛸", layout="wide")

# SF 스타일 커스텀 CSS (강조 색상 변경)
st.markdown("""
<style>
    .stProgress > div > div > div > div { background-color: #00ffcc; }
</style>
""", unsafe_allow_html=True)

st.title("🛸 지구 방위 사령부: 심우주 탐색 대시보드")
st.markdown("### 인류의 새로운 개척지를 분석하고 기록하는 메인 프레임입니다.")
st.markdown("---")

# 2. NASA API 데이터 로딩 (발견 연도, 발견 방법 추가)
@st.cache_data(ttl=86400)
def load_nasa_data():
    # discoverymethod, disc_year 추가
    query = "select pl_name, sy_dist, pl_masse, pl_eqt, ra, dec, discoverymethod, disc_year from ps where default_flag=1 and sy_dist is not null"
    url = f"https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query={urllib.parse.quote(query)}&format=csv"
    
    df = pd.read_csv(url)
    
    # 데이터 전처리
    df['Distance (LY)'] = df['sy_dist'] * 3.26156 
    df['Temperature (°C)'] = df['pl_eqt'] - 273.15 
    df['Mass (Earths)'] = df['pl_masse'].fillna(df['pl_masse'].median())
    df['Temperature (°C)'] = df['Temperature (°C)'].fillna(df['Temperature (°C)'].median())
    
    # 3D 좌표 변환
    ra_rad = np.radians(df['ra'])
    dec_rad = np.radians(df['dec'])
    dist = df['Distance (LY)']
    
    df['X'] = dist * np.cos(dec_rad) * np.cos(ra_rad)
    df['Y'] = dist * np.cos(dec_rad) * np.sin(ra_rad)
    df['Z'] = dist * np.sin(dec_rad)
    
    # 거주 가능 지수
    temp_score = np.abs(df['Temperature (°C)'] - 15) * 0.3
    mass_score = np.abs(df['Mass (Earths)'] - 1) * 2
    df['Habitability Score'] = 100 - temp_score - mass_score
    df['Habitability Score'] = df['Habitability Score'].clip(lower=0, upper=100)
    
    df.rename(columns={'pl_name': 'Planet Name', 'discoverymethod': 'Discovery Method', 'disc_year': 'Discovery Year'}, inplace=True)
    return df

with st.spinner("메인 프레임 가동 중... NASA 신경망에 접속합니다... 🌐"):
    raw_df = load_nasa_data()

# 3. 사이드바 컨트롤러
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e5/NASA_logo.svg", width=100)
st.sidebar.header("📡 레이더 제어반")
max_distance = st.sidebar.slider("스캔 반경 (광년)", 10, int(raw_df['Distance (LY)'].max()), 3000, 50)
selected_methods = st.sidebar.multiselect(
    "탐지 방식 필터", 
    options=raw_df['Discovery Method'].unique(),
    default=raw_df['Discovery Method'].unique()[:3]
)

df = raw_df[(raw_df['Distance (LY)'] <= max_distance) & (raw_df['Discovery Method'].isin(selected_methods))]

# 👇 --- 여기에 안전장치 코드를 추가하세요! --- 👇
if df.empty:
    st.warning("⚠️ 레이더에 잡히는 행성이 없습니다. 좌측 제어반에서 탐지 방식을 하나 이상 선택해 주세요.")
    st.stop() # 이후의 차트/통계 계산 코드를 실행하지 않고 여기서 멈춥니다.
# 👆 -------------------------------------- 👆

# 4. 상단 핵심 지표
col1, col2, col3, col4 = st.columns(4)
col1.metric("가용 외계 행성 데이터", f"{len(df):,} 개")
col2.metric("최초 발견 연도", f"{int(df['Discovery Year'].min())}년")
col3.metric("초거대 행성 (>10 지구질량)", f"{len(df[df['Mass (Earths)'] > 10])} 개")
col4.metric("테라포밍 유망 후보", f"{len(df[df['Habitability Score'] > 80])} 개")
st.markdown("---")

# 5. 탭(Tabs)을 이용한 화면 분할
tab1, tab2, tab3 = st.tabs(["🌐 3D 은하 성도", "📈 탐사 통계 분석", "🪪 외계 행성 여권"])

with tab1:
    st.subheader(f"섹터 반경 {max_distance:,} 광년 전술 지도")
    fig_3d = px.scatter_3d(
        df, x='X', y='Y', z='Z', color='Habitability Score', size='Mass (Earths)',
        hover_name='Planet Name', hover_data=['Distance (LY)', 'Temperature (°C)'],
        color_continuous_scale=px.colors.sequential.Aggrnyl, # 레이더 느낌의 형광 녹색 톤
        opacity=0.7, size_max=15
    )
    fig_3d.update_layout(
        scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False),
        paper_bgcolor='black', plot_bgcolor='black', margin=dict(l=0, r=0, b=0, t=0)
    )
    st.plotly_chart(fig_3d, use_container_width=True)

with tab2:
    st.subheader("인류의 심우주 개척 역사")
    c1, c2 = st.columns(2)
    with c1:
        # 연도별 발견 수 (히스토그램)
        fig_year = px.histogram(df, x="Discovery Year", title="연도별 외계 행성 발견 수", color_discrete_sequence=['#00ffcc'])
        fig_year.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_year, use_container_width=True)
    with c2:
        # 발견 방법 비율 (도넛 차트)
        fig_method = px.pie(df, names="Discovery Method", title="행성 탐지 기술 비율", hole=0.4)
        fig_method.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_method, use_container_width=True)

with tab3:
    st.subheader("외계 행성 상세 분석 (Planet Passport)")
    selected_planet = st.selectbox("탐색할 행성 이름을 입력하거나 선택하세요:", df['Planet Name'].sort_values())
    
    planet_data = df[df['Planet Name'] == selected_planet].iloc[0]
    
    # SF 스타일 상태 메시지 생성기
    temp = planet_data['Temperature (°C)']
    if temp < -50:
        status, color = "❄️ 극저온 환경: 방한 장비 및 열원 필수", "blue"
    elif temp > 100:
        status, color = "🔥 초고온 환경: 텅스텐 합금 우주선 외에는 접근 불가", "red"
    else:
        status, color = "🌿 생명체 거주 가능성 존재: 정밀 탐사 권장", "green"

    st.markdown(f"### 대상: **{selected_planet}**")
    st.markdown(f":{color}[**분석 결과: {status}**]")
    
    pc1, pc2, pc3, pc4 = st.columns(4)
    pc1.metric("지구로부터 거리", f"{planet_data['Distance (LY)']:.1f} 광년")
    pc2.metric("질량 (지구 대비)", f"{planet_data['Mass (Earths)']:.2f} 배")
    pc3.metric("표면 온도", f"{temp:.1f} °C")
    pc4.metric("거주 가능 지수", f"{planet_data['Habitability Score']:.0f} / 100")
    
    # 프로그래스 바 시각화
    st.write("거주 가능 지수 게이지:")
    st.progress(int(planet_data['Habitability Score']))
