import streamlit as st

def run():
    st.markdown("# 🧪 신제품개발시스템")
    st.markdown("##### 시장 정보 분석부터 개발보고서까지 신제품 개발 전 과정을 지원합니다.")
    st.markdown("---")

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
        st.info("계열 트렌드 분석 + 최근 N개월 비교 + YoY + 계절성 분석 + 플레이버 쇼핑 분석")

        import requests, json, urllib.parse, pandas as pd
        from datetime import date

        if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
            st.error("⚠️ 네이버 API secrets가 설정되지 않았습니다.")
            return

        # ─────────────
        # 계열 정의
        # ─────────────
        beverage_groups = {
            "탄산음료": ["콜라","사이다","이온음료","무알콜음료","과즙탄산음료","아이스티음료","에이드음료"],
            "과일주스": ["오렌지주스","사과주스","포도주스","망고주스","자몽주스","감귤주스","레몬주스","타트체리주스"],
            "건강기능성음료": ["에너지음료","비타민음료","단백질음료"],
            "전통/차음료": ["식혜","수정과","녹차음료","홍차음료","곡물음료","쌍화차"],
            "우유/요거트/대체유": ["우유","요거트","아몬드우유","귀리우유","두유"],
            "제로/저당음료": ["제로음료","저당음료","무설탕음료"]
        }

        selected_group = st.selectbox("📂 분석 계열 선택", list(beverage_groups.keys()))
        flavor_input = st.text_input("🍊 플레이버 입력", placeholder="망고, 레몬, 저당 등")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", date(2023,1,1))
        with col2:
            end_date = st.date_input("종료일", date.today())

        time_unit = st.selectbox("기간 단위", ["month","week","date"])
        recent_n = st.selectbox("최근 N개월 비교", [3,6,12])

        if st.button("📊 분석 실행"):

            keywords = beverage_groups[selected_group]

            body = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "timeUnit": time_unit,
                "keywordGroups": [
                    {"groupName": selected_group, "keywords": keywords}
                ]
            }

            response = requests.post(
                "https://openapi.naver.com/v1/datalab/search",
                headers={
                    "X-Naver-Client-Id": st.secrets["naver_search"]["NAVER_CLIENT_ID"],
                    "X-Naver-Client-Secret": st.secrets["naver_search"]["NAVER_CLIENT_SECRET"],
                    "Content-Type": "application/json"
                },
                data=json.dumps(body)
            )

            if response.status_code != 200:
                st.error(response.text)
                return

            df = pd.DataFrame(response.json()["results"][0]["data"])
            df["period"] = pd.to_datetime(df["period"])
            df = df.sort_values("period")

            st.subheader("📈 트렌드 그래프")
            st.line_chart(df.set_index("period")["ratio"])

            # ─────────────
            # B. 최근 N개월 비교
            # ─────────────
            if time_unit == "month" and len(df) >= recent_n:
                df_recent = df.tail(recent_n)
                growth_n = (df_recent["ratio"].iloc[-1] - df_recent["ratio"].iloc[0]) / df_recent["ratio"].iloc[0] * 100
                st.metric(f"최근 {recent_n}개월 성장률", f"{growth_n:.1f}%")

            # ─────────────
            # C. YoY 분석
            # ─────────────
            if time_unit == "month" and len(df) >= 13:
                df["YoY"] = df["ratio"].pct_change(12) * 100
                st.subheader("📊 전년 동기 대비 (YoY %)")
                st.line_chart(df.set_index("period")["YoY"])

            # ─────────────
            # D. 계절성 분석
            # ─────────────
            if time_unit == "month":
                df["month"] = df["period"].dt.month
                seasonal = df.groupby("month")["ratio"].mean()
                st.subheader("🌦 계절성 분석 (월 평균)")
                st.bar_chart(seasonal)

            # ─────────────
            # 플레이버 쇼핑 분석
            # ─────────────
            if flavor_input:
                search_query = f"{selected_group} {flavor_input}"
                enc = urllib.parse.quote(search_query)
                shop_url = f"https://openapi.naver.com/v1/search/shop.json?query={enc}&display=100"

                shop_response = requests.get(
                    shop_url,
                    headers={
                        "X-Naver-Client-Id": st.secrets["naver_shopping"]["NAVER_CLIENT_ID"],
                        "X-Naver-Client-Secret": st.secrets["naver_shopping"]["NAVER_CLIENT_SECRET"]
                    }
                )

                if shop_response.status_code == 200:
                    df_shop = pd.DataFrame(shop_response.json()["items"])
                    df_shop["lprice"] = pd.to_numeric(df_shop["lprice"], errors="coerce")

                    st.subheader("💰 평균 가격")
                    st.metric("평균가", f"{df_shop['lprice'].mean():,.0f} 원")

                    st.subheader("🏷 브랜드 TOP5")
                    st.bar_chart(df_shop["brand"].value_counts().head(5))

                    st.subheader("📂 세부 카테고리 분포")
                    st.bar_chart(df_shop["category3"].value_counts())

    # ─────────────────────────────────────────────
    # 기존 탭 유지
    # ─────────────────────────────────────────────
    with tabs[1]:
        st.markdown("### 🧬 배합비개발")
        st.text_area("배합비 메모", height=120)
        if st.button("영양성분 자동 계산", key="A_calc"):
            st.success("계산 기능 연동 예정입니다.")

    with tabs[2]:
        st.markdown("### ⚠️ 공정리스크확인")
        st.selectbox("공정 단계 선택", ["원료 입고","세척/선별","가공/혼합","살균/멸균","충전/포장","출하"])
        if st.button("리스크 평가 실행", key="A_risk"):
            st.warning("리스크 평가 기능 연동 예정입니다.")

    with tabs[3]:
        st.markdown("### 📋 생산계획서")
        col1, col2 = st.columns(2)
        with col1:
            st.date_input("생산 시작일")
        with col2:
            st.number_input("생산 수량 (개)", min_value=0, value=1000, step=100)
        if st.button("계획서 생성", key="A_plan"):
            st.success("생산계획서 생성 기능 연동 예정입니다.")

    with tabs[4]:
        st.markdown("### 📝 개발보고서")
        st.text_input("제품명")
        if st.button("보고서 자동 생성", key="A_report"):
            st.success("보고서 생성 기능 연동 예정입니다.")
