import streamlit as st
import requests, json, urllib.parse
import pandas as pd
import plotly.graph_objects as go
from datetime import date

try:
    from openai import OpenAI
except:
    OpenAI = None


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

    # ============================================================
    # 📈 시장정보분석 (AI 통합 보고서 버전)
    # ============================================================
    with tabs[0]:

        st.markdown("## 📊 전략 비교 대시보드")

        if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
            st.error("네이버 API secrets가 설정되지 않았습니다.")
            return

        openai_enabled = False
        if "openai" in st.secrets:
            try:
                from openai import OpenAI
                openai_enabled = True
            except:
                openai_enabled = False

        # ─────────────────────────────
        # 계열 정의
        # ─────────────────────────────
        beverage_groups = {
            "탄산음료": ["콜라","사이다","이온음료","과즙탄산음료","에이드음료"],
            "과일주스": ["오렌지주스","사과주스","포도주스","망고주스","레몬주스","타트체리주스"],
            "건강기능성음료": ["에너지음료","비타민음료","단백질음료"],
            "전통/차음료": ["식혜","쌍화차","녹차음료","홍차음료"],
            "우유/요거트/대체유": ["우유","요거트","두유","아몬드우유","귀리우유"],
            "제로/저당음료": ["제로음료","저당음료","무설탕음료"]
        }

        selected_groups = st.multiselect(
            "📂 분석 계열 (복수 선택 가능)",
            list(beverage_groups.keys())
        )

        flavor_input = st.text_input("🍊 플레이버 (선택)", placeholder="망고, 레몬 등")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일")
        with col2:
            end_date = st.date_input("종료일")

        time_unit = st.selectbox("📅 분석 단위", ["month","week","date"])

        if st.button("📊 분석 실행"):

            # ============================================================
            # 1️⃣ 트렌드 분석
            # ============================================================
            trend_summary = {}
            plot_data = {}

            for group in selected_groups:

                keywords = beverage_groups[group]

                body = {
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d"),
                    "timeUnit": time_unit,
                    "keywordGroups": [
                        {"groupName": group, "keywords": keywords}
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
                    continue

                result = response.json()

                if "results" not in result:
                    continue

                df = pd.DataFrame(result["results"][0]["data"])
                if df.empty:
                    continue

                df["period"] = pd.to_datetime(df["period"])
                plot_data[group] = df

                trend_summary[group] = df["ratio"].tolist()[-3:]

            # Plotly 그래프
            import plotly.graph_objects as go
            fig = go.Figure()

            for name, df_data in plot_data.items():
                fig.add_trace(
                    go.Scatter(
                        x=df_data["period"],
                        y=df_data["ratio"],
                        mode="lines+markers",
                        name=name
                    )
                )

            st.plotly_chart(fig, use_container_width=True)

            # ============================================================
            # 2️⃣ 네이버 쇼핑 검색 순위 분석
            # ============================================================
            shopping_summary = {}

            if flavor_input:

                enc = urllib.parse.quote(flavor_input)
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

                    shopping_summary = {
                        "평균가격": float(df_shop["lprice"].mean()),
                        "상위브랜드": df_shop["brand"].value_counts().head(5).to_dict(),
                        "판매처분포": df_shop["mallName"].value_counts().head(5).to_dict()
                    }

                    st.subheader("🛍 쇼핑 제품 현황")
                    st.dataframe(df_shop[["title","lprice","brand","mallName"]])

            # ============================================================
            # 3️⃣ AI 통합 전략 보고서
            # ============================================================
            if openai_enabled:

                st.subheader("🤖 AI 통합 전략 보고서")
                st.markdown("**AI 모델: gpt-4o-mini**")

                with st.spinner("AI 통합 분석 보고서 생성 중..."):

                    client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

                    prompt = f"""
                    다음은 음료 시장 트렌드 요약 데이터입니다:
                    {trend_summary}

                    다음은 네이버 쇼핑 검색 결과 요약입니다:
                    {shopping_summary}

                    위 두 데이터를 통합하여:
                    1. 시장 성장 해석
                    2. 가격 포지셔닝 전략
                    3. 유망 플레이버 방향
                    4. 브랜드 전략 제안
                    5. 실행 전략

                    보고서 형식으로 작성하세요.
                    """

                    response_ai = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role":"user","content":prompt}]
                    )

                st.write(response_ai.choices[0].message.content)

            else:
                st.info("OpenAI 키가 없어 통합 AI 보고서가 비활성화됩니다.")


        # ─────────────────────────────
        # 계열 정의
        # ─────────────────────────────
        beverage_groups = {
            "탄산음료": ["콜라","사이다","이온음료","과즙탄산음료","에이드음료"],
            "과일주스": ["오렌지주스","사과주스","포도주스","망고주스","레몬주스","타트체리주스"],
            "건강기능성음료": ["에너지음료","비타민음료","단백질음료"],
            "전통/차음료": ["식혜","쌍화차","녹차음료","홍차음료"],
            "우유/요거트/대체유": ["우유","요거트","두유","아몬드우유","귀리우유"],
            "제로/저당음료": ["제로음료","저당음료","무설탕음료"]
        }

        selected_groups = st.multiselect(
            "📂 분석 계열 (복수 선택 가능)",
            list(beverage_groups.keys())
        )

        sub_candidates = []
        for g in selected_groups:
            sub_candidates.extend(beverage_groups[g])

        selected_sub = st.multiselect(
            "📁 하위 카테고리 (복수 선택 가능)",
            sub_candidates
        )

        flavor_input = st.text_input("🍊 플레이버 (선택)", placeholder="망고, 레몬 등")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", date(2023,1,1))
        with col2:
            end_date = st.date_input("종료일", date.today())

        time_unit = st.selectbox("📅 분석 단위", ["month","week","date"])

        # ============================================================
        # 분석 실행
        # ============================================================
        if st.button("📊 분석 실행"):

            compare_targets = selected_sub if selected_sub else selected_groups

            if not compare_targets:
                st.warning("계열 또는 하위 카테고리를 선택하세요.")
                return

            data_dict = {}

            for target in compare_targets:

                # 🔥 계열 선택 시 내부 키워드 묶음 처리
                if target in beverage_groups:
                    keywords = beverage_groups[target]
                else:
                    keywords = [target]

                body = {
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d"),
                    "timeUnit": time_unit,
                    "keywordGroups": [
                        {"groupName": target, "keywords": keywords}
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
                    continue

                result = response.json()

                if "results" not in result or len(result["results"]) == 0:
                    continue

                df = pd.DataFrame(result["results"][0]["data"])

                if df.empty or "period" not in df.columns:
                    continue

                df["period"] = pd.to_datetime(df["period"])
                data_dict[target] = df

            if not data_dict:
                st.warning("유효한 트렌드 데이터가 없습니다.")
                return

            # ─────────────────────────────
            # Plotly 비교 그래프
            # ─────────────────────────────
            fig = go.Figure()

            for name, df_data in data_dict.items():
                fig.add_trace(
                    go.Scatter(
                        x=df_data["period"],
                        y=df_data["ratio"],
                        mode="lines+markers",
                        name=name,
                        hovertemplate="항목: %{fullData.name}<br>기간: %{x}<br>관심도: %{y:.2f}<extra></extra>"
                    )
                )

            fig.update_layout(
                title="📈 트렌드 비교",
                xaxis_title="기간",
                yaxis_title="상대 관심도",
                legend_title="비교 항목",
                hovermode="x unified"
            )

            st.plotly_chart(fig, use_container_width=True)

            # ─────────────────────────────
            # AI 전략 해석
            # ─────────────────────────────
            if openai_enabled:

                client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

                summary_data = {k: v["ratio"].tolist()[-3:] for k, v in data_dict.items()}

                prompt = f"""
                다음은 음료 트렌드 최근 데이터입니다:
                {summary_data}

                성장 관점 전략 인사이트를 5줄 요약하세요.
                """

                response_ai = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}]
                )

                st.subheader("🤖 AI 전략 해석")
                st.write(response_ai.choices[0].message.content)

            # ─────────────────────────────
            # 플레이버 쇼핑 분석
            # ─────────────────────────────
            if flavor_input:

                enc = urllib.parse.quote(flavor_input)

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

    # ============================================================
    # 기존 탭 유지
    # ============================================================
    with tabs[1]:
        st.markdown("### 🧬 배합비개발")

    with tabs[2]:
        st.markdown("### ⚠️ 공정리스크확인")

    with tabs[3]:
        st.markdown("### 📋 생산계획서")

    with tabs[4]:
        st.markdown("### 📝 개발보고서")
