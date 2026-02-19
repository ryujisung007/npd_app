import streamlit as st
import requests
import json
import urllib.parse
import pandas as pd
import plotly.graph_objects as go
from datetime import date

try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def run():

    st.markdown("# 🧪 신제품개발시스템")
    st.markdown("##### 시장 정보 분석부터 개발보고서까지 신제품 개발 전 과정을 지원합니다.")
    st.markdown("---")

    # ─────────────────────────────
    # 상단 요약 지표 (기존 유지)
    # ─────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📈 진행 중 프로젝트", "147")
    c2.metric("🧬 배합비 개발 중", "32")
    c3.metric("⚠️ 리스크 항목", "5")
    c4.metric("📋 완료 보고서", "89")

    st.markdown("<br>", unsafe_allow_html=True)

    tabs = st.tabs(
        ["📈 시장정보분석", "🧬 배합비개발", "⚠️ 공정리스크확인", "📋 생산계획서", "📝 개발보고서"]
    )

    # ============================================================
    # 📈 시장정보분석
    # ============================================================
    with tabs[0]:

        st.markdown("## 📊 음료 시장 전략 분석")

        if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
            st.error("네이버 API secrets가 설정되지 않았습니다.")
            return

        openai_enabled = False
        if "openai" in st.secrets and OpenAI is not None:
            openai_enabled = True

        beverage_groups = {
            "탄산음료": ["콜라", "사이다", "이온음료", "과즙탄산음료"],
            "과일주스": ["오렌지주스", "사과주스", "망고주스", "레몬주스"],
            "건강기능성음료": ["에너지음료", "비타민음료", "단백질음료"],
            "전통/차음료": ["식혜", "녹차음료", "홍차음료"],
            "제로/저당음료": ["제로음료", "저당음료", "무설탕음료"],
        }

        selected_groups = st.multiselect(
            "📂 분석 계열", list(beverage_groups.keys())
        )

        flavor_input = st.text_input("🍊 플레이버(쇼핑 분석용)", placeholder="예: 망고")

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", date(2023, 1, 1))
        with col2:
            end_date = st.date_input("종료일", date.today())

        time_unit = st.selectbox("📅 분석 단위", ["month", "week", "date"])

        if st.button("📊 분석 실행"):

            if not selected_groups:
                st.warning("계열을 선택하세요.")
                return

            trend_summary = {}
            plot_data = {}

            # --------------------------------------------------------
            # 1️⃣ DataLab 트렌드 분석
            # --------------------------------------------------------
            for group in selected_groups:

                body = {
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d"),
                    "timeUnit": time_unit,
                    "keywordGroups": [
                        {
                            "groupName": group,
                            "keywords": beverage_groups[group],
                        }
                    ],
                }

                response = requests.post(
                    "https://openapi.naver.com/v1/datalab/search",
                    headers={
                        "X-Naver-Client-Id": st.secrets["naver_search"]["NAVER_CLIENT_ID"],
                        "X-Naver-Client-Secret": st.secrets["naver_search"]["NAVER_CLIENT_SECRET"],
                        "Content-Type": "application/json",
                    },
                    data=json.dumps(body),
                )

                if response.status_code != 200:
                    continue

                result = response.json()
                if "results" not in result:
                    continue

                df = pd.DataFrame(result["results"][0]["data"])
                df["period"] = pd.to_datetime(df["period"])

                plot_data[group] = df
                trend_summary[group] = df["ratio"].tolist()[-3:]

            # Plot
            fig = go.Figure()
            for name, df_data in plot_data.items():
                fig.add_trace(
                    go.Scatter(
                        x=df_data["period"],
                        y=df_data["ratio"],
                        mode="lines+markers",
                        name=name,
                    )
                )

            fig.update_layout(
                title="계열별 트렌드 비교",
                hovermode="x unified",
            )

            st.plotly_chart(fig, use_container_width=True)

            # --------------------------------------------------------
            # 2️⃣ 쇼핑 상품 분석
            # --------------------------------------------------------
            shopping_summary = {}
            brand_rank = None

            if flavor_input:

                enc = urllib.parse.quote(flavor_input)

                shop_response = requests.get(
                    f"https://openapi.naver.com/v1/search/shop.json?query={enc}&display=100",
                    headers={
                        "X-Naver-Client-Id": st.secrets["naver_shopping"]["NAVER_CLIENT_ID"],
                        "X-Naver-Client-Secret": st.secrets["naver_shopping"]["NAVER_CLIENT_SECRET"],
                    },
                )

                if shop_response.status_code == 200:

                    df_shop = pd.DataFrame(shop_response.json()["items"])
                    df_shop["lprice"] = pd.to_numeric(df_shop["lprice"], errors="coerce")

                    st.subheader("🛍 쇼핑 상품 현황")
                    st.dataframe(df_shop[["title", "lprice", "brand", "mallName"]])

                    st.metric("평균 가격", f"{df_shop['lprice'].mean():,.0f} 원")

                    # 브랜드 순위
                    brand_rank = (
                        df_shop["brand"]
                        .value_counts()
                        .reset_index()
                    )
                    brand_rank.columns = ["브랜드", "노출건수"]

                    st.subheader("🏆 브랜드 노출 순위")
                    st.dataframe(brand_rank)

                    st.bar_chart(brand_rank.set_index("브랜드")["노출건수"])

                    # 상위 10위 브랜드
                    top10 = df_shop.head(10)
                    st.subheader("🔝 상위 10개 브랜드 점유")
                    st.bar_chart(top10["brand"].value_counts())

                    # 브랜드 평균 가격
                    st.subheader("💰 브랜드 평균 가격")
                    st.bar_chart(
                        df_shop.groupby("brand")["lprice"]
                        .mean()
                        .sort_values(ascending=False)
                    )

                    shopping_summary = {
                        "평균가격": float(df_shop["lprice"].mean()),
                        "브랜드순위": brand_rank.to_dict(),
                    }

            # --------------------------------------------------------
            # 3️⃣ AI 통합 보고서
            # --------------------------------------------------------
            if openai_enabled:

                st.markdown(
                    "<div style='font-size:18px;font-weight:600;margin-top:20px;'>"
                    "🤖 AI 통합 전략 보고서</div>",
                    unsafe_allow_html=True,
                )

                st.markdown(
                    "<div style='font-size:12px;color:gray;'>"
                    "AI 모델: gpt-4o-mini</div>",
                    unsafe_allow_html=True,
                )

                with st.spinner("AI 전략 보고서 생성 중..."):

                    client = OpenAI(
                        api_key=st.secrets["openai"]["OPENAI_API_KEY"]
                    )

                    prompt = f"""
                    트렌드 데이터:
                    {trend_summary}

                    쇼핑 데이터:
                    {shopping_summary}

                    위 내용을 기반으로 시장 성장성,
                    브랜드 경쟁 구조,
                    가격 전략,
                    신규 진입 전략을 종합 보고서로 작성하세요.
                    """

                    response_ai = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                    )

                st.markdown(
                    f"""
                    <div style='
                        background:#F4F6F8;
                        padding:20px;
                        border-radius:10px;
                        font-size:14px;
                        line-height:1.6;
                        color:#222;
                    '>
                    {response_ai.choices[0].message.content}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:
                st.info("OpenAI 키가 없어 AI 보고서는 비활성화됩니다.")

    # ============================================================
    # 기존 탭 유지
    # ============================================================
    with tabs[1]:
        st.markdown("### 🧬 배합비개발")
        st.text_area("배합비 메모", height=120)

    with tabs[2]:
        st.markdown("### ⚠️ 공정리스크확인")
        st.selectbox("공정 단계 선택", ["원료 입고", "가공", "포장", "출하"])

    with tabs[3]:
        st.markdown("### 📋 생산계획서")
        st.date_input("생산 시작일")
        st.number_input("생산 수량", min_value=0, value=1000)

    with tabs[4]:
        st.markdown("### 📝 개발보고서")
        st.text_input("제품명")
