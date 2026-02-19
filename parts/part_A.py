import streamlit as st
import requests
import json
import urllib.parse
import pandas as pd
import plotly.graph_objects as go
from datetime import date

# OpenAI는 선택적 로드 (없어도 앱이 죽지 않도록)
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
    # 📈 시장정보분석 (트렌드 + 쇼핑 + AI 통합 보고서)
    # ============================================================
    with tabs[0]:

        st.markdown("## 📊 전략 비교 대시보드")

        # ─────────────────────────────
        # API 키 체크
        # ─────────────────────────────
        if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
            st.error("네이버 API secrets가 설정되지 않았습니다.")
            return

        openai_enabled = False
        if "openai" in st.secrets and OpenAI is not None:
            openai_enabled = True

        # ─────────────────────────────
        # 음료 계열 정의
        # ─────────────────────────────
        beverage_groups = {
            "탄산음료": ["콜라", "사이다", "이온음료", "과즙탄산음료", "에이드음료"],
            "과일주스": ["오렌지주스", "사과주스", "포도주스", "망고주스", "레몬주스", "타트체리주스"],
            "건강기능성음료": ["에너지음료", "비타민음료", "단백질음료"],
            "전통/차음료": ["식혜", "쌍화차", "녹차음료", "홍차음료"],
            "우유/요거트/대체유": ["우유", "요거트", "두유", "아몬드우유", "귀리우유"],
            "제로/저당음료": ["제로음료", "저당음료", "무설탕음료"],
        }

        # ─────────────────────────────
        # 사용자 입력
        # ─────────────────────────────
        selected_groups = st.multiselect(
            "📂 분석 계열 (복수 선택 가능)",
            list(beverage_groups.keys()),
        )

        flavor_input = st.text_input(
            "🍊 플레이버 (선택)",
            placeholder="예: 망고, 레몬, 저당 등",
        )

        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("시작일", date(2023, 1, 1))
        with col2:
            end_date = st.date_input("종료일", date.today())

        time_unit = st.selectbox("📅 분석 단위", ["month", "week", "date"])

        # ============================================================
        # 분석 실행
        # ============================================================
        if st.button("📊 분석 실행"):

            if not selected_groups:
                st.warning("최소 1개 이상의 분석 계열을 선택하세요.")
                return

            trend_summary = {}
            plot_data = {}

            # ------------------------------------------------------------
            # 1️⃣ 트렌드 분석 (DataLab)
            # ------------------------------------------------------------
            for group in selected_groups:

                keywords = beverage_groups[group]

                body = {
                    "startDate": start_date.strftime("%Y-%m-%d"),
                    "endDate": end_date.strftime("%Y-%m-%d"),
                    "timeUnit": time_unit,
                    "keywordGroups": [
                        {"groupName": group, "keywords": keywords}
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

                if "results" not in result or len(result["results"]) == 0:
                    continue

                df = pd.DataFrame(result["results"][0]["data"])
                if df.empty:
                    continue

                df["period"] = pd.to_datetime(df["period"])
                plot_data[group] = df

                trend_summary[group] = df["ratio"].tolist()[-3:]

            if not plot_data:
                st.warning("트렌드 데이터를 가져오지 못했습니다.")
                return

            # Plotly 비교 그래프
            fig = go.Figure()
            for name, df_data in plot_data.items():
                fig.add_trace(
                    go.Scatter(
                        x=df_data["period"],
                        y=df_data["ratio"],
                        mode="lines+markers",
                        name=name,
                        hovertemplate="항목: %{fullData.name}<br>기간: %{x}<br>관심도: %{y:.2f}<extra></extra>",
                    )
                )

            fig.update_layout(
                title="📈 계열별 트렌드 비교",
                xaxis_title="기간",
                yaxis_title="상대 관심도",
                legend_title="비교 계열",
                hovermode="x unified",
            )

            st.plotly_chart(fig, use_container_width=True)

                    # ============================================================
        # 2️⃣ 네이버 쇼핑 트렌드 분석 (카테고리 기반)
        # ============================================================

        shopping_trend_summary = {}

        if flavor_input:

            category_body = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate": end_date.strftime("%Y-%m-%d"),
                "timeUnit": time_unit,
                "category": [
                    {
                        "name": flavor_input,
                        "param": ["50000000"]  # 식품 카테고리 (예시 코드)
                    }
                ]
            }

            shopping_trend_response = requests.post(
                "https://openapi.naver.com/v1/datalab/shopping/categories",
                headers={
                    "X-Naver-Client-Id": st.secrets["naver_search"]["NAVER_CLIENT_ID"],
                    "X-Naver-Client-Secret": st.secrets["naver_search"]["NAVER_CLIENT_SECRET"],
                    "Content-Type": "application/json",
                },
                data=json.dumps(category_body),
            )

            if shopping_trend_response.status_code == 200:
                result = shopping_trend_response.json()

                if "results" in result:
                    df_shop_trend = pd.DataFrame(result["results"][0]["data"])
                    df_shop_trend["period"] = pd.to_datetime(df_shop_trend["period"])

                    st.subheader("🛒 쇼핑 트렌드 흐름")
                    st.line_chart(df_shop_trend.set_index("period")["ratio"])

                    shopping_trend_summary = df_shop_trend["ratio"].tolist()[-3:]

                        # ============================================================
            # 3️⃣ AI 통합 전략 보고서 (가독성 개선)
            # ============================================================

            if openai_enabled:

                st.markdown("""
                <div style='font-size:18px;font-weight:700;margin-top:20px;'>
                🤖 AI 통합 전략 보고서
                </div>
                """, unsafe_allow_html=True)

                st.markdown("<div style='font-size:13px;color:gray;'>AI 모델: gpt-4o-mini</div>", unsafe_allow_html=True)

                with st.spinner("AI 통합 분석 보고서 생성 중..."):

                    client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

                    prompt = f"""
                    트렌드 데이터:
                    {trend_summary}

                    쇼핑 상품 요약:
                    {shopping_summary}

                    쇼핑 트렌드 데이터:
                    {shopping_trend_summary}

                    위 데이터를 통합하여 전략 보고서를 작성하세요.
                    """

                    response_ai = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                    )

                st.markdown(
                    f"""
                    <div style='
                        background-color:#F4F6F8;
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


    # ============================================================
    # 이하 기존 탭 구조 그대로 유지
    # ============================================================
    with tabs[1]:
        st.markdown("### 🧬 배합비개발")
        st.text_area("배합비 메모", height=120)
        if st.button("영양성분 자동 계산", key="A_calc"):
            st.success("계산 기능 연동 예정입니다.")

    with tabs[2]:
        st.markdown("### ⚠️ 공정리스크확인")
        st.selectbox(
            "공정 단계 선택",
            ["원료 입고", "세척/선별", "가공/혼합", "살균/멸균", "충전/포장", "출하"],
        )
        if st.button("리스크 평가 실행", key="A_risk"):
            st.warning("리스크 평가 기능 연동 예정입니다.")

    with tabs[3]:
        st.markdown("### 📋 생산계획서")
        col1, col2 = st.columns(2)
        with col1:
            st.date_input("생산 시작일")
        with col2:
            st.number_input(
                "생산 수량 (개)", min_value=0, value=1000, step=100
            )
        if st.button("계획서 생성", key="A_plan"):
            st.success("생산계획서 생성 기능 연동 예정입니다.")

    with tabs[4]:
        st.markdown("### 📝 개발보고서")
        st.text_input("제품명")
        if st.button("보고서 자동 생성", key="A_report"):
            st.success("보고서 생성 기능 연동 예정입니다.")
