import streamlit as st
import requests
import json
import urllib.parse
import pandas as pd
import plotly.graph_objects as go
from datetime import date
from io import BytesIO

# PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.units import inch

try:
    from openai import OpenAI
except:
    OpenAI = None


def run():

    st.markdown("# 🧪 신제품개발시스템")
    st.markdown("---")
    st.markdown("## 📊 음료 시장 전략 통합 대시보드")

    # ============================================================
    # 확장된 음료 DB
    # ============================================================

    beverage_structure = {

        "탄산/청량음료": {
            "플레이버": [
                "콜라","제로콜라","라임","자몽","청포도",
                "유자","복숭아","파인애플","망고",
                "딸기","레몬","체리"
            ],
            "브랜드": [
                "코카콜라","코카콜라제로","펩시","펩시제로",
                "칠성사이다","환타","스프라이트","탐스"
            ]
        },

        "과일주스/NFC": {
            "플레이버": [
                "오렌지","망고","사과","포도","자몽",
                "파인애플","타트체리","블루베리",
                "아로니아","레몬","복숭아","석류"
            ],
            "브랜드": [
                "델몬트","썬키스트","따옴","돈시몬",
                "웅진","미닛메이드"
            ]
        },

        "건강기능성/프로틴": {
            "플레이버": [
                "초코","바닐라","쿠키앤크림",
                "베리믹스","망고프로틴","그린티",
                "흑임자","콜라겐레몬"
            ],
            "브랜드": [
                "마이밀","셀시어스","닥터유",
                "몬스터","레드불","하이뮨"
            ]
        },

        "차/전통음료": {
            "플레이버": [
                "녹차","홍차","보리차","옥수수차",
                "헛개차","식혜","쌍화차","대추차"
            ],
            "브랜드": [
                "광동","동서","웅진","담터"
            ]
        },

        "제로/저당": {
            "플레이버": [
                "제로콜라","제로사이다",
                "무가당레몬","저당망고","무설탕자몽"
            ],
            "브랜드": [
                "코카콜라제로","펩시제로",
                "칠성제로","탐스제로"
            ]
        }
    }

    # ============================================================
    # UI 입력부
    # ============================================================

    selected_group = st.selectbox(
        "📂 분석계열",
        list(beverage_structure.keys())
    )

    # 플레이버
    col1, col2 = st.columns([2,1])
    with col1:
        flavor_select = st.selectbox(
            "🍊 추천 플레이버",
            beverage_structure[selected_group]["플레이버"],
            key="flavor_select"
        )
    with col2:
        flavor_custom = st.text_input(
            "직접 입력 (플레이버)",
            key="flavor_custom"
        )

    final_flavor = flavor_custom.strip() if flavor_custom else flavor_select

    # 브랜드
    col3, col4 = st.columns([2,1])
    with col3:
        brand_select = st.selectbox(
            "🏷 추천 브랜드",
            beverage_structure[selected_group]["브랜드"],
            key="brand_select"
        )
    with col4:
        brand_custom = st.text_input(
            "직접 입력 (브랜드)",
            key="brand_custom"
        )

    final_brand = brand_custom.strip() if brand_custom else brand_select

    # ============================================================
    # 실행
    # ============================================================

    if st.button("📊 전략 분석 실행"):

        if not final_flavor and not final_brand:
            st.warning("⚠ 플레이버 또는 브랜드를 선택해야 쇼핑 데이터가 출력됩니다.")
            return

        # AND 검색
        if final_flavor and final_brand:
            search_keyword = f"{final_brand} {final_flavor}"
        elif final_flavor:
            search_keyword = final_flavor
        else:
            search_keyword = final_brand

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

        # ============================================================
        # 전략 지표 계산
        # ============================================================

        brand_share = df_shop["brand"].value_counts(normalize=True) * 100
        dominance_index = brand_share.iloc[0] * len(df_shop)
        avg_price = df_shop["lprice"].mean()
        median_price = df_shop["lprice"].median()

        df_shop["price_position"] = df_shop["lprice"].apply(
            lambda x: "프리미엄" if x > median_price else "가성비"
        )

        opportunity_score = (100 - brand_share.iloc[0]) * (1 if avg_price < median_price else 0.8)

        if opportunity_score > 60:
            strategy_grade = "A"
        elif opportunity_score > 35:
            strategy_grade = "B"
        else:
            strategy_grade = "C"

        # ============================================================
        # 카드뉴스 출력
        # ============================================================

        st.markdown("### 📰 전략 카드뉴스")

        colA, colB = st.columns(2)

        with colA:
            st.markdown("#### 🏷 브랜드 점유율")
            st.bar_chart(brand_share)

        with colB:
            st.markdown("#### 💰 평균 가격")
            st.metric("평균가", f"{avg_price:,.0f} 원")

        colC, colD = st.columns(2)

        with colC:
            st.markdown("#### 📊 프리미엄 vs 가성비")
            st.bar_chart(df_shop["price_position"].value_counts())

        with colD:
            st.markdown("#### 🧮 브랜드 지배력 지수")
            st.metric("지배력지수", f"{dominance_index:.1f}")

        st.markdown("### 🚀 신규 진입 기회")
        st.metric("Opportunity Score", f"{opportunity_score:.1f}")
        st.metric("전략 등급", strategy_grade)

        # ============================================================
        # AI 전략 보고서
        # ============================================================

        if "openai" in st.secrets and OpenAI:

            client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

            with st.spinner("AI 전략 보고서 생성 중..."):

                prompt = f"""
                브랜드 점유율: {brand_share.to_dict()}
                평균가격: {avg_price}
                지배력지수: {dominance_index}
                신규진입점수: {opportunity_score}
                전략등급: {strategy_grade}

                위 데이터를 기반으로 전문적인 전략 보고서를 작성하세요.
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                )

            report_text = response.choices[0].message.content

            st.markdown("## 📊 AI 통합 전략 보고서")
            st.markdown(report_text)

            # ========================================================
            # PDF 생성
            # ========================================================

            def generate_pdf(text):
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer)
                pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
                styles = getSampleStyleSheet()
                style = styles["Normal"]
                style.fontName = "HYSMyeongJo-Medium"
                style.fontSize = 11
                elements = []
                elements.append(Paragraph("AI 통합 전략 보고서", style))
                elements.append(Spacer(1, 0.3 * inch))
                elements.append(Paragraph(text.replace("\n", "<br/>"), style))
                doc.build(elements)
                buffer.seek(0)
                return buffer

            pdf_buffer = generate_pdf(report_text)

            st.download_button(
                label="📄 전략 보고서 PDF 다운로드",
                data=pdf_buffer,
                file_name="AI_전략보고서.pdf",
                mime="application/pdf"
            )
