import streamlit as st
from parts import part_A_market, part_A_formula, part_A_risk, part_A_plan, part_A_report


def run():
    st.markdown("## 🧪 신제품개발시스템")
    st.caption("시장 정보 분석부터 개발보고서까지 신제품 개발 전 과정을 지원합니다.")
    st.markdown("---")

    # KPI 요약
    k1, k2, k3, k4 = st.columns(4)
    for col, label, value in [
        (k1, "📈 진행 중 프로젝트", "147"),
        (k2, "🧬 배합비 개발 중",   "32"),
        (k3, "⚠️ 리스크 항목",      "5"),
        (k4, "📋 완료 보고서",       "89"),
    ]:
        col.metric(label, value)

    st.markdown("<br>", unsafe_allow_html=True)

    tabs = st.tabs([
        "📈 시장정보분석",
        "🧬 배합비개발",
        "⚠️ 공정리스크확인",
        "📋 생산계획서",
        "📝 개발보고서",
    ])

    with tabs[0]:
        part_A_market.run()

    with tabs[1]:
        part_A_formula.run()

    with tabs[2]:
        part_A_risk.run()

    with tabs[3]:
        part_A_plan.run()

    with tabs[4]:
        part_A_report.run()