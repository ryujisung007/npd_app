import streamlit as st

def run():
    st.markdown("# 🧪 신제품개발시스템")
    st.markdown("##### 시장 정보 분석부터 개발보고서까지 신제품 개발 전 과정을 지원합니다.")
    st.markdown("---")

    # 요약 지표
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📈 진행 중 프로젝트", "147")
    c2.metric("🧬 배합비 개발 중", "32")
    c3.metric("⚠️ 리스크 항목", "5")
    c4.metric("📋 완료 보고서", "89")

    st.markdown("<br>", unsafe_allow_html=True)

    # 서브메뉴 탭
    tabs = st.tabs(["📈 시장정보분석", "🧬 배합비개발", "⚠️ 공정리스크확인", "📋 생산계획서", "📝 개발보고서"])

    with tabs[0]:
        st.markdown("### 📈 시장정보분석")
        st.info("네이버 쇼핑 API 기반 식품 카테고리 시장 현황 및 트렌드를 실시간으로 분석합니다.")
        col1, col2 = st.columns([3,1])
        with col1:
            keyword = st.text_input("🔍 검색 키워드", placeholder="예: 라면, 음료, 과자...")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("수집 시작", key="A_search"):
                st.success(f"'{keyword}' 수집을 시작합니다.")

    with tabs[1]:
        st.markdown("### 🧬 배합비개발")
        st.info("원재료 배합 비율을 설계하고 최적 조합을 도출합니다. 영양성분 자동 계산 포함.")
        st.text_area("배합비 메모", placeholder="원재료 및 비율을 입력하세요...", height=120)
        if st.button("영양성분 자동 계산", key="A_calc"):
            st.success("계산 기능 연동 예정입니다.")

    with tabs[2]:
        st.markdown("### ⚠️ 공정리스크확인")
        st.info("HACCP 기반 공정별 위해요소를 점검하고 리스크 레벨을 평가합니다.")
        st.selectbox("공정 단계 선택", ["원료 입고", "세척/선별", "가공/혼합", "살균/멸균", "충전/포장", "출하"])
        if st.button("리스크 평가 실행", key="A_risk"):
            st.warning("리스크 평가 기능 연동 예정입니다.")

    with tabs[3]:
        st.markdown("### 📋 생산계획서")
        st.info("개발 일정, 원재료 소요량, 생산 수량 계획을 자동으로 문서화합니다.")
        col1, col2 = st.columns(2)
        with col1:
            st.date_input("생산 시작일")
        with col2:
            st.number_input("생산 수량 (개)", min_value=0, value=1000, step=100)
        if st.button("계획서 생성", key="A_plan"):
            st.success("생산계획서 생성 기능 연동 예정입니다.")

    with tabs[4]:
        st.markdown("### 📝 개발보고서")
        st.info("전 과정의 개발 결과를 종합하여 보고서를 자동 생성합니다.")
        st.text_input("제품명", placeholder="보고서를 생성할 제품명 입력")
        if st.button("보고서 자동 생성", key="A_report"):
            st.success("보고서 생성 기능 연동 예정입니다.")
