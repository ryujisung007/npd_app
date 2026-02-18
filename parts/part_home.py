import streamlit as st

def run():
    st.markdown("# 🍱 AI 식품정보 시스템")
    st.markdown("##### 파트를 선택하여 시작하세요. 각 파트는 독립적으로 운영됩니다.")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    cards = [
        (col1, "🧪", "Part A", "신제품개발시스템", "시장정보분석 · 배합비개발 · 공정리스크확인 · 생산계획서 · 개발보고서", "#00C8D4"),
        (col2, "📊", "Part B", "시장조사 시스템",  "식품시장현황분석 · 품목제조보고분석 · 신제품 매출 집계", "#FFB830"),
        (col3, "👥", "Part C", "소비자조사",       "가상페르소나 만들기 · 관능검사 시스템 · 제품 컨셉 점수분석", "#B08FFF"),
    ]
    for col, icon, badge, title, desc, color in cards:
        with col:
            st.markdown(f"""
            <div style="background:#1A2E4A;border:1px solid #1E3A5A;border-radius:12px;
                        padding:22px;border-top:3px solid {color};min-height:160px;">
                <div style="font-size:1.8rem;margin-bottom:8px">{icon}</div>
                <span style="background:rgba(0,200,212,0.15);color:{color};
                      font-size:0.7rem;font-weight:700;padding:2px 9px;border-radius:6px">{badge}</span>
                <div style="font-size:1.05rem;font-weight:900;color:#fff;margin:10px 0 6px">{title}</div>
                <div style="font-size:0.78rem;color:#7A9CC0;line-height:1.65">{desc}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col4, col5, _ = st.columns(3)
    cards2 = [
        (col4, "🗄️", "Part D", "DB 검색시스템", "자료등록 · 자료분류 · 자료현황보기", "#FF6B6B"),
        (col5, "📚", "Part F", "러닝시스템",    "AI 학습 기반 식품 정보 자동화 서비스 (준비 중)", "#4DFFB4"),
    ]
    for col, icon, badge, title, desc, color in cards2:
        with col:
            st.markdown(f"""
            <div style="background:#1A2E4A;border:1px solid #1E3A5A;border-radius:12px;
                        padding:22px;border-top:3px solid {color};min-height:160px;">
                <div style="font-size:1.8rem;margin-bottom:8px">{icon}</div>
                <span style="background:rgba(0,200,212,0.15);color:{color};
                      font-size:0.7rem;font-weight:700;padding:2px 9px;border-radius:6px">{badge}</span>
                <div style="font-size:1.05rem;font-weight:900;color:#fff;margin:10px 0 6px">{title}</div>
                <div style="font-size:0.78rem;color:#7A9CC0;line-height:1.65">{desc}</div>
            </div>""", unsafe_allow_html=True)
