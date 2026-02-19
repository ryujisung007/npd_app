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

    tabs = st.tabs(["📈 시장정보분석", "🧬 배합비개발", "⚠️ 공정리스크확인", "📋 생산계획서", "📝 개발보고서"])

    # ─────────────────────────────────────────────
    # 📈 시장정보분석
    # ─────────────────────────────────────────────
    with tabs[0]:
        st.markdown("### 📈 시장정보분석")
        st.info("네이버 DataLab + 쇼핑 API 기반 음료 시장 트렌드를 분석합니다.")

        import requests, json, urllib.parse, pandas as pd

        # 🔐 secrets 안전 체크
        if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
            st.error("⚠️ 네이버 API secrets가 설정되지 않았습니다.")
            st.info("로컬 실행 시 .streamlit/secrets.toml 파일을 생성하세요.")
            return

        col1, col2 = st.columns([3,1])
        with col1:
            keyword = st.text_input("🔍 키워드 (콤마 구분)", value="음료,제로음료,단백질음료")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            run_btn = st.button("수집 시작", key="A_search")

        if run_btn:

            keyword_list = [k.strip() for k in keyword.split(",")]

            # ─────────────
            # 1️⃣ DataLab 분석
            # ─────────────
            url = "https://openapi.naver.com/v1/datalab/search"

            body = {
                "startDate": "2024-01-01",
                "endDate": "2025-01-01",
                "timeUnit": "month",
                "keywordGroups": [
                    {
                        "groupName": "음료",
                        "keywords": keyword_list
                    }
                ]
            }

            headers = {
                "X-Naver-Client-Id": st.secrets["naver_search"]["NAVER_CLIENT_ID"],
                "X-Naver-Client-Secret": st.secrets["naver_search"]["NAVER_CLIENT_SECRET"],
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, data=json.dumps(body))

            if response.status_code == 200:

                result = response.json()
                df_trend = pd.DataFrame(result["results"][0]["data"])

                st.subheader("📊 검색어 트렌드")
                st.line_chart(df_trend.set_index("period")["ratio"])

                df_trend["growth_rate"] = df_trend["ratio"].pct_change()

                # ─────────────
                # 2️⃣ 쇼핑 분석 연결
                # ─────────────
                selected_keyword = st.selectbox("쇼핑 분석 키워드 선택", keyword_list)

                if st.button("선택 키워드 쇼핑 분석"):

                    encText = urllib.parse.quote(selected_keyword)
                    shop_url = f"https://openapi.naver.com/v1/search/shop.json?query={encText}&display=100"

                    shop_headers = {
                        "X-Naver-Client-Id": st.secrets["naver_shopping"]["NAVER_CLIENT_ID"],
                        "X-Naver-Client-Secret": st.secrets["naver_shopping"]["NAVER_CLIENT_SECRET"]
                    }

                    shop_response = requests.get(shop_url, headers=shop_headers)

                    if shop_response.status_code == 200:

                        df_shop = pd.DataFrame(shop_response.json()["items"])
                        df_shop["lprice"] = pd.to_numeric(df_shop["lprice"], errors="coerce")

                        st.subheader("💰 평균 가격")
                        st.metric("평균가", f"{df_shop['lprice'].mean():,.0f} 원")

                        st.subheader("🏷 브랜드 TOP5")
                        st.bar_chart(df_shop["brand"].value_counts().head(5))

                        st.subheader("📂 세부 카테고리 분포")
                        st.bar_chart(df_shop["category3"].value_counts())

                        st.subheader("📋 상세 데이터")
                        st.dataframe(df_shop[["title","lprice","brand","category3"]])

                    else:
                        st.error(shop_response.text)

            else:
                st.error(response.text)

    # ─────────────────────────────────────────────
    # 이하 기존 코드 그대로 유지
    # ─────────────────────────────────────────────
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
