import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import time

# 1. 페이지 설정 (넓은 화면, 기본 다크 모드 최적화)
st.set_page_config(
    page_title="Galactic Explorer",
    page_icon="🌌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 멋진 헤더 타이틀
st.title("🌌 은하계 외계 행성 탐색기 (Galactic Exoplanet Explorer)")
st.markdown("### 인류의 새로운 터전을 찾아서... 광활한 우주를 탐색하세요. 🚀")
st.markdown("---")

# 3. 사이드바 컨트롤러 (탐색 필터)
st.sidebar.header("📡 탐색 레이더 설정")
num_planets = st.sidebar.slider("탐색할 행성의 수", min_value=100, max_value=5000, value=1000, step=100)
scan_radius = st.sidebar.slider("탐색 반경 (광년)", min_value=10, max_value=10000, value=5000, step=10)

# 가상 데이터 생성 함수 (캐싱하여 속도 최적화)
@st.cache_data
def generate_universe_data(num, radius):
    np.random.seed(42)
    # 우주 좌표 (X, Y, Z)
    x = np.random.normal(0, radius, num)
    y = np.random.normal(0, radius, num)
    z = np.random.normal(0, radius / 5, num) # 은하계는 원반 형태이므로 Z축은 얇게
    
    # 행성 특성
    mass = np.random.uniform(0.1, 50.0, num) # 지구 질량 배수
    temp = np.random.uniform(-200, 500, num) # 표면 온도 (섭씨)
    
    # 거주 가능 지수 (Habitability Score: 0~100) - 지구(15도, 질량1)와 비슷할수록 높음
    habitability = 100 - (np.abs(temp - 15) * 0.3) - (np.abs(mass - 1) * 2)
    habitability = np.clip(habitability, 0, 100)
    
    # 행성 이름 생성기
    prefixes = ["Kepler", "Gliese", "TRAPPIST", "HD", "K2"]
    names = [f"{np.random.choice(prefixes)}-{np.random.randint(100, 9999)}{chr(np.random.randint(97, 102))}" for _ in range(num)]
    
    return pd.DataFrame({
        "Planet Name": names, "X": x, "Y": y, "Z": z,
        "Mass (Earths)": mass, "Temperature (°C)": temp, "Habitability Score": habitability
    })

# 4. 데이터 로딩 연출
with st.spinner("심우주 스캔 중... 양자 컴퓨터가 데이터를 분석하고 있습니다... 궤도 계산 중..."):
    time.sleep(1.5) # 극적인 효과를 위한 약간의 딜레이
    df = generate_universe_data(num_planets, scan_radius)

# 5. 핵심 지표 (Metrics) 표시
st.subheader("📊 실시간 관측 브리핑")
col1, col2, col3, col4 = st.columns(4)

high_habitable = len(df[df["Habitability Score"] > 80])
avg_temp = df["Temperature (°C)"].mean()

col1.metric("총 스캔된 행성", f"{num_planets:,} 개")
col2.metric("탐색 반경", f"{scan_radius:,} 광년")
col3.metric("거주 가능성 높음 (>80점)", f"{high_habitable} 개", "인류 생존 가능성 발견!")
col4.metric("평균 표면 온도", f"{avg_temp:.1f} °C")

st.markdown("---")

# 6. 메인 시각화: 3D 우주 지도 (가장 멋있는 부분)
st.subheader("🌐 3D 은하 성도 (Interactive Star Map)")
st.markdown("마우스로 지도를 회전하거나 줌인/줌아웃하여 외계 행성의 위치를 직접 확인해보세요.")

fig = px.scatter_3d(
    df, x='X', y='Y', z='Z',
    color='Habitability Score',
    size='Mass (Earths)',
    hover_name='Planet Name',
    hover_data=['Temperature (°C)', 'Mass (Earths)'],
    color_continuous_scale=px.colors.sequential.Plasma,
    opacity=0.8,
    title="Sector 7G 주변 외계 행성 분포도"
)

# 3D 차트 배경을 우주처럼 검게 만들기
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

# 7. 데이터 테이블 및 마무리
st.subheader("📋 세부 관측 데이터")
st.dataframe(df.sort_values(by="Habitability Score", ascending=False).head(100), use_container_width=True)

st.success("스캔 완료! 우주의 신비는 아직 끝이 없습니다.")
# 깜짝 이벤트 (처음 실행 시 풍선 효과)
if 'loaded' not in st.session_state:
    st.balloons()
    st.session_state['loaded'] = True
