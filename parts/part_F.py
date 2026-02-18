import streamlit as st

def run():
    st.markdown("# 📚 러닝시스템")
    st.markdown("##### AI 학습 기반 식품 정보 자동화 서비스 — 현재 개발 중입니다.")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    cards = [
        (col1, "🤖", "AI 자동 분류", "업로드한 식품 데이터를 AI가 자동으로 카테고리 분류합니다.", "#4DFFB4"),
        (col2, "📖", "학습 데이터 관리", "모델 학습에 사용된 데이터셋을 관리하고 성능을 모니터링합니다.", "#00C8D4"),
        (col3, "📈", "학습 성능 리포트", "각 AI 모델의 정확도, F1 스코어 등 성능 지표를 시각화합니다.", "#B08FFF"),
    ]
    for col, icon, title, desc, color in cards:
        with col:
            st.markdown(f"""
            <div style="background:#1A2E4A;border:1px solid #1E3A5A;border-radius:12px;
                        padding:22px;border-top:3px solid {color}">
                <div style="font-size:1.8rem;margin-bottom:10px">{icon}</div>
                <div style="font-size:1rem;font-weight:800;color:#fff;margin-bottom:6px">{title}</div>
                <div style="font-size:0.78rem;color:#7A9CC0;line-height:1.6">{desc}</div>
                <div style="margin-top:12px;font-size:0.7rem;font-weight:700;
                     background:rgba(77,255,180,0.1);color:{color};
                     padding:3px 10px;border-radius:8px;display:inline-block">준비 중</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.info("🚧 러닝시스템은 다른 파트의 데이터가 충분히 축적된 후 순차적으로 개발될 예정입니다.")
