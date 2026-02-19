import streamlit as st

st.set_page_config(
    page_title="AI 식품정보 시스템",
    page_icon="🍱",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("TEST OK")


# ── 공통 CSS ──
st.markdown("""
<style>
/* 전체 배경 */
[data-testid="stAppViewContainer"] { background: #0B1629; }
[data-testid="stSidebar"] { background: #142036 !important; border-right: 1px solid #1E3A5A; }
[data-testid="stSidebar"] * { color: #E8F0FE !important; }

/* 사이드바 상단 강조선 */
[data-testid="stSidebar"]::before {
    content:''; display:block; height:3px;
    background: linear-gradient(90deg,#00C8D4,#B08FFF);
}

/* 사이드바 라디오 버튼 */
div[role="radiogroup"] label {
    font-size: 1rem !important;
    font-weight: 600 !important;
    padding: 8px 4px !important;
    white-space: nowrap !important;
}

/* 메트릭 카드 */
[data-testid="metric-container"] {
    background: #1A2E4A;
    border: 1px solid #1E3A5A;
    border-radius: 10px;
    padding: 14px !important;
}
[data-testid="stMetricValue"] { color: #00F0FF !important; font-size: 1.6rem !important; font-weight: 900 !important; }
[data-testid="stMetricLabel"] { color: #7A9CC0 !important; font-size: 0.8rem !important; }

/* 일반 텍스트 */
h1,h2,h3 { color: #FFFFFF !important; }
p, li     { color: #E8F0FE !important; }

/* selectbox/text_input */
[data-testid="stSelectbox"] > div,
[data-testid="stTextInput"] > div > div {
    background: #1A2E4A !important;
    border: 1px solid #1E3A5A !important;
    color: #E8F0FE !important;
    border-radius: 8px !important;
}

/* 버튼 */
[data-testid="stButton"] > button {
    background: #00C8D4 !important;
    color: #0B1629 !important;
    font-weight: 800 !important;
    border: none !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
}
[data-testid="stButton"] > button:hover { background: #00F0FF !important; }

/* dataframe */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* 구분선 */
hr { border-color: #1E3A5A !important; }

/* 탭 */
[data-testid="stTab"] { background: #142036 !important; }
button[data-baseweb="tab"] { color: #7A9CC0 !important; font-size:0.9rem !important; font-weight:600 !important; }
button[data-baseweb="tab"][aria-selected="true"] { color: #00C8D4 !important; border-bottom-color: #00C8D4 !important; }
</style>
""", unsafe_allow_html=True)

# ── 사이드바 ──
with st.sidebar:
    st.markdown("### 🍱 AI 식품정보 시스템")
    st.caption("ver 1.0 · Food Intelligence")
    st.markdown("---")

    part = st.radio(
        "📁 Part 선택",
        options=["🏠 홈", "🧪 A | 신제품개발시스템", "📊 B | 시장조사 시스템",
                 "👥 C | 소비자조사", "🗄️ D | DB 검색시스템", "📚 F | 러닝시스템"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.caption("각 파트는 독립적으로 운영됩니다.")

# ── 파트 라우팅 (독립 모듈) ──
try:
    if part.startswith("🏠"):
        from parts import part_home as mod
    elif part.startswith("🧪"):
        from parts import part_A as mod
    elif part.startswith("📊"):
        from parts import part_B as mod
    elif part.startswith("👥"):
        from parts import part_C as mod
    elif part.startswith("🗄️"):
        from parts import part_D as mod
    elif part.startswith("📚"):
        from parts import part_F as mod
    mod.run()
except Exception as e:
    st.error(f"⚠️ 해당 파트 로드 중 오류: {e}")
    st.info("다른 파트는 정상적으로 작동합니다.")
