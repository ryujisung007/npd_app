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

    # 상단 요약 지표
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

        # 스타일 개선
        st.markdown("""
        <style>
        .report-box {
            background:#1A2332;
            padding:25px;
            border-radius:12px;
            font-size:14px;
            line-height:1.7;
            color:#E0E6ED;
            box-shadow:0px 4px 12px rgba(0,0,0,0.3);
        }
        .report-title {
            color:#00D4FF;
            font-size:18px;
            font-weight:600;
            margin-bottom:15px;
        }
        </style>
        """, unsafe_allow_html=True)

        if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
            st.error("네이버 API secrets가 설정되지 않았습니다.")
            return

        openai_enabled = False
        if "openai" in st.secrets and OpenAI is not None:
            openai_enabled = True

        beverage_structure = {
            "건강기능성음료": {
                "플레이버": ["망고", "베리", "레몬", "복숭아", "초코"],
                "브랜드": ["몬스터", "레드불", "셀시어스", "마이밀"]
            },
            "탄산음료": {
                "플레이버": ["콜라", "레몬", "자몽", "라임"],
                "브랜드": ["코카콜라", "펩시", "칠성사이다"]
            },
            "과일주스": {
                "플레이버": ["오렌지", "사과", "망고", "포도"],
                "브랜드": ["델몬트", "썬키스트", "따옴"]
            }
        }

        # ───────────────
        # 계열 선택
        # ───────────────
        selected_group = st.selectbox(
            "📂 분석 계열",
            list(beverage_structure.keys())
        )

        # ───────────────
        # 플레이버
        # ───────────────
        st.markdown("### 🍊 플레이버 선택")

        col1, col2 = st.columns([2,1])
        with col1:
            flavor_select = st.selectbox(
                "추천 플레이버",
                beverage_structure[selected_group]["플레이버"]
            )
        with col2:
            flavor_custom = st.text_input("직접 입력")

        final_flavor = flavor_custom if flavor_custom else flavor_select

        # ───────────────
        # 브랜드
        # ───────────────
        st.markdown("### 🏷 브랜드 선택")

        col3, col4 = st.columns([2,1])
        with col3:
            brand_select = st.selectbox(
                "추천 브랜드",
                beverage_structure[selected_group]["브랜드"]
            )
        with col4:
            brand_custom = st.text_input("직접 입력 ")

        final_brand = brand_custom if brand_custom else brand_select

        # ───────────────
        # 기간 선택
        # ───────────────
        col5, col6 = st.columns(2)
        with col5:
            start_date = st.date_input("시작일", date(2023,1,1))
        with col6:
            end_date = st.date_input("종료일", date.today())

        time_unit = st.selectbox("📅 분석 단위", ["month", "week", "date"])

        # ───────────────
        # 실행 버튼
        # ───────────────
        if st.button("📊 분석 실행"):

            if not final_flavor and not final_brand:
                st.warning("⚠ 플레이버나 브랜드를 선택하셔야, 쇼핑데이터가 출력됩니다.")
                return

            search_keyword = final_flavor if final_flavor else final_brand

            # --------------------------------------------------------
            # 쇼핑 데이터 수집
            # --------------------------------------------------------
            enc = urllib.parse.quote(search_keyword)

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

            st.subheader("🛍 쇼핑 상품 현황")
            st.dataframe(df_shop[["title", "lprice", "brand", "mallName"]])

            st.metric("평균 가격", f"{df_shop['lprice'].mean():,.0f} 원")

            # 브랜드 노출 순위
            brand_rank = df_shop["brand"].value_counts().reset_index()
            brand_rank.columns = ["브랜드", "노출건수"]

            st.subheader("🏆 브랜드 노출 순위")
            st.dataframe(brand_rank)

            st.bar_chart(brand_rank.set_index("브랜드")["노출건수"])

            # 상위 10위 브랜드
            st.subheader("🔝 상위 10개 브랜드 점유")
            st.bar_chart(df_shop.head(10)["brand"].value_counts())

            # 브랜드 평균 가격
            st.subheader("💰 브랜드 평균 가격")
            st.bar_chart(
                df_shop.groupby("brand")["lprice"]
                .mean()
                .sort_values(ascending=False)
            )

            # --------------------------------------------------------
            # AI 통합 보고서
            # --------------------------------------------------------
            if openai_enabled:

                st.markdown('<div class="report-title">🤖 AI 통합 전략 보고서</div>', unsafe_allow_html=True)
                st.markdown("<div style='font-size:12px;color:gray;'>AI 모델: gpt-4o-mini</div>", unsafe_allow_html=True)

                with st.spinner("AI 전략 보고서 생성 중..."):

                    client = OpenAI(
                        api_key=st.secrets["openai"]["OPENAI_API_KEY"]
                    )

                    prompt = f"""
                    쇼핑 데이터 요약:
                    평균가격: {df_shop['lprice'].mean()}
                    브랜드 순위: {brand_rank.to_dict()}

                    위 데이터를 기반으로 시장 경쟁구조, 가격 전략,
                    유망 플레이버 방향, 신규 진입 전략을 제안하세요.
                    """

                    response_ai = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                    )

                st.markdown(
                    f"<div class='report-box'>{response_ai.choices[0].message.content}</div>",
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
