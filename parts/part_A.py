import streamlit as st
import requests
import json
import urllib.parse
import pandas as pd
import plotly.express as px
from datetime import date
from io import BytesIO

try:
    from openai import OpenAI
except:
    OpenAI = None


def run():

    st.markdown("# 🧪 신제품개발시스템")
    st.markdown("##### 시장정보분석 · 배합비개발 · 공정리스크확인 · 생산계획서 · 개발보고서")
    st.markdown("---")

    # ============================================================
    # 탭 복원
    # ============================================================

    tabs = st.tabs([
        "📈 시장정보분석",
        "🧬 배합비개발",
        "⚠️ 공정리스크확인",
        "📋 생산계획서",
        "📝 개발보고서"
    ])

    # ============================================================
    # 📈 시장정보분석
    # ============================================================

    with tabs[0]:

        st.subheader("📊 네이버 DataLab 음료 트렌드 분석")

        beverage_structure = {
            "탄산/청량음료": ["콜라","제로콜라","사이다","에이드","자몽"],
            "과일주스": ["오렌지","망고","사과","타트체리","블루베리"],
            "건강기능성": ["단백질음료","비타민음료","콜라겐","프로틴초코"],
            "차/전통": ["녹차","식혜","쌍화차","헛개차"]
        }

        col1, col2 = st.columns(2)

        with col1:
            selected_group = st.selectbox(
                "분석계열 선택",
                list(beverage_structure.keys())
            )

        with col2:
            selected_flavors = st.multiselect(
                "플레이버 복수 선택",
                beverage_structure[selected_group]
            )

        start_date = st.date_input("시작일", value=date(2024,1,1))
        end_date = st.date_input("종료일", value=date.today())

        if st.button("📈 트렌드 분석 실행"):

            if not selected_flavors:
                st.warning("플레이버를 선택하세요.")
                return

            # ----------------------------
            # DataLab API 호출
            # ----------------------------

            url = "https://openapi.naver.com/v1/datalab/search"

            body = {
                "startDate": str(start_date),
                "endDate": str(end_date),
                "timeUnit": "month",
                "keywordGroups": [
                    {"groupName": f, "keywords": [f]}
                    for f in selected_flavors
                ]
            }

            headers = {
                "X-Naver-Client-Id": st.secrets["naver_search"]["NAVER_CLIENT_ID"],
                "X-Naver-Client-Secret": st.secrets["naver_search"]["NAVER_CLIENT_SECRET"],
                "Content-Type": "application/json"
            }

            response = requests.post(url, headers=headers, data=json.dumps(body))

            if response.status_code != 200:
                st.error(response.text)
                return

            result = response.json()

            df_total = pd.DataFrame()

            for r in result["results"]:
                df = pd.DataFrame(r["data"])
                df["keyword"] = r["title"]
                df_total = pd.concat([df_total, df])

            # ----------------------------
            # 그래프 출력
            # ----------------------------

            fig = px.line(
                df_total,
                x="period",
                y="ratio",
                color="keyword",
                markers=True
            )

            fig.update_layout(
                height=450,
                legend_title="플레이버"
            )

            st.plotly_chart(fig, use_container_width=True)

            # ----------------------------
            # 시장지수 계산
            # ----------------------------

            market_index = df_total.groupby("keyword")["ratio"].mean()
            st.write("### 📊 평균 시장지수")
            st.dataframe(market_index)

            # ========================================================
            # AI 트렌드 분석
            # ========================================================

            if "openai" in st.secrets and OpenAI:

                client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

                with st.spinner("AI 트렌드 분석 중..."):

                    prompt = f"""
                    다음은 음료 트렌드 지수 데이터입니다.
                    {market_index.to_dict()}

                    시장 트렌드 분석 보고서를 작성하세요.
                    """

                    response_ai = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role":"user","content":prompt}]
                    )

                trend_report = response_ai.choices[0].message.content

                st.markdown("## 🧠 AI 트렌드 분석 보고서")
                st.markdown(trend_report)

            # ========================================================
            # 쇼핑 분석 자동 연결
            # ========================================================

            st.markdown("---")
            st.subheader("🛒 네이버 쇼핑 시장 분석")

            top_keyword = market_index.idxmax()
            st.info(f"최상위 트렌드 키워드 자동 선택: {top_keyword}")

            enc = urllib.parse.quote(top_keyword)

            shop_response = requests.get(
                f"https://openapi.naver.com/v1/search/shop.json?query={enc}&display=100",
                headers={
                    "X-Naver-Client-Id": st.secrets["naver_shopping"]["NAVER_CLIENT_ID"],
                    "X-Naver-Client-Secret": st.secrets["naver_shopping"]["NAVER_CLIENT_SECRET"],
                }
            )

            if shop_response.status_code != 200:
                st.error(shop_response.text)
                return

            df_shop = pd.DataFrame(shop_response.json()["items"])
            df_shop["lprice"] = pd.to_numeric(df_shop["lprice"], errors="coerce")

            brand_share = df_shop["brand"].value_counts().head(10)

            colA, colB = st.columns(2)

            with colA:
                st.markdown("### 🏷 브랜드 점유")
                st.bar_chart(brand_share)

            with colB:
                st.markdown("### 💰 가격 분포")
                st.bar_chart(df_shop["lprice"].head(20))

            # ========================================================
            # AI 통합 전략 보고서
            # ========================================================

            if "openai" in st.secrets and OpenAI:

                with st.spinner("AI 통합 전략 보고서 생성 중..."):

                    prompt2 = f"""
                    트렌드 지수: {market_index.to_dict()}
                    브랜드 점유: {brand_share.to_dict()}

                    통합 전략 보고서를 작성하세요.
                    """

                    response_ai2 = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role":"user","content":prompt2}]
                    )

                final_report = response_ai2.choices[0].message.content

                st.markdown("## 📊 AI 통합 전략 보고서")
                st.markdown(final_report)

                # HTML 다운로드
                st.download_button(
                    label="📄 보고서 다운로드",
                    data=final_report,
                    file_name="전략보고서.txt"
                )

    # ============================================================
    # 나머지 탭 복원
    # ============================================================

    with tabs[1]:
        st.subheader("🧬 배합비개발")
        st.text_area("배합비 설계 입력")

    with tabs[2]:
        st.subheader("⚠️ 공정리스크확인")
        st.selectbox("공정 단계 선택", ["원료 입고","가공","살균","포장"])

    with tabs[3]:
        st.subheader("📋 생산계획서")
        st.date_input("생산 시작일")

    with tabs[4]:
        st.subheader("📝 개발보고서")
        st.text_input("제품명 입력")
