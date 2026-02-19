import streamlit as st
from openai import OpenAI

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

        # UI 강조 CSS
        st.markdown("""
        <style>
        div[data-baseweb="select"] * {
            font-weight: 700 !important;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("### 📈 시장정보분석")
        st.info("계열 트렌드 분석 + 세부 비교 + AI 전략 해석 포함")

        import requests, json, urllib.parse, pandas as pd
        from datetime import date

        if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
            st.error("⚠️ 네이버 API secrets가 설정되지 않았습니다.")
            return

        beverage_groups = {
            "탄산음료": ["콜라","사이다","이온음료","과즙탄산음료","에이드음료"],
            "과일주스": ["오렌지주스","사과주스","포도주스","망고주스","레몬주스","타트체리주스"],
            "건강기능성음료": ["에너지음료","비타민음료","단백질음료"],
            "전통/차음료": ["식혜","쌍화차","녹차음료","홍차음료"],
            "우유/요거트/대체유": ["우유","요거트","두유","아몬드우유","귀리우유"],
            "제로/저당음료": ["제로음료","저당음료","무설탕음료"]
        }

        selected_group = st.selectbox("📂 분석 계열", list(beverage_groups.keys()))
        flavor_input = st.text_input("🍊 플레이버 (선택사항)", placeholder="예: 망고, 레몬, 저당 등")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", date(2023,1,1))
        with col2:
            end_date = st.date_input("종료일", date.today())

        time_unit = st.selectbox("📅 분석 단위", ["month","week","date"])

        if st.button("📊 분석 실행"):

            keywords = beverage_groups[selected_group]

            # ─────────────
            # 1️⃣ 플레이버 없을 경우: 세부항목 비교
            # ─────────────
            if not flavor_input:

                growth_dict = {}

                for kw in keywords:
                    body = {
                        "startDate": start_date.strftime("%Y-%m-%d"),
                        "endDate": end_date.strftime("%Y-%m-%d"),
                        "timeUnit": time_unit,
                        "keywordGroups": [
                            {"groupName": kw, "keywords": [kw]}
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

                    if response.status_code == 200:
                        df = pd.DataFrame(response.json()["results"][0]["data"])
                        df["ratio"] = pd.to_numeric(df["ratio"])
                        growth = df["ratio"].iloc[-1]
                        growth_dict[kw] = growth

                df_compare = pd.DataFrame.from_dict(growth_dict, orient="index", columns=["ratio"])
                df_compare = df_compare.sort_values("ratio", ascending=False)

                st.subheader("📊 세부 카테고리 상대 비교")
                st.bar_chart(df_compare)

                # AI 분석
                client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

                prompt = f"""
                다음은 {selected_group} 세부항목 트렌드 상대수치입니다:
                {df_compare.to_dict()}

                성장 관점에서 전략적 인사이트를 5줄 요약하세요.
                """

                response_ai = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}]
                )

                st.subheader("🤖 AI 전략 해석")
                st.write(response_ai.choices[0].message.content)

            # ─────────────
            # 2️⃣ 플레이버 있을 경우: 상세 트렌드
            # ─────────────
            else:

                body = {
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d"),
                    "timeUnit": time_unit,
                    "keywordGroups": [
                        {"groupName": flavor_input, "keywords": [flavor_input]}
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

                if response.status_code == 200:
                    df = pd.DataFrame(response.json()["results"][0]["data"])
                    df["period"] = pd.to_datetime(df["period"])

                    st.subheader("📈 플레이버 트렌드")
                    st.line_chart(df.set_index("period")["ratio"])

                    # AI 해석
                    client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

                    prompt = f"""
                    다음은 {flavor_input} 트렌드 데이터입니다:
                    {df.tail(6).to_dict()}

                    최근 흐름과 제품 전략 시사점을 요약하세요.
                    """

                    response_ai = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role":"user","content":prompt}]
                    )

                    st.subheader("🤖 AI 전략 해석")
                    st.write(response_ai.choices[0].message.content)

                # 쇼핑 분석
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

    # ─────────────────────────────────────────────
    # 기존 탭 유지
    # ─────────────────────────────────────────────
    with tabs[1]:
        st.markdown("### 🧬 배합비개발")
        st.text_area("배합비 메모", height=120)

    with tabs[2]:
        st.markdown("### ⚠️ 공정리스크확인")

    with tabs[3]:
        st.markdown("### 📋 생산계획서")

    with tabs[4]:
        st.markdown("### 📝 개발보고서")
