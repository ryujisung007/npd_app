import streamlit as st
import requests
import urllib.parse
import pandas as pd
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

    # ============================================================
    # 시장정보분석
    # ============================================================
    st.markdown("## 📊 전략 통합 대시보드")

    beverage_structure = {
        "건강기능성음료": {
            "플레이버": ["망고", "베리", "레몬", "복숭아", "초코", "프로틴초코", "콜라겐베리"],
            "브랜드": ["몬스터", "레드불", "마이밀", "셀시어스", "닥터유"]
        },
        "탄산음료": {
            "플레이버": ["콜라", "라임", "자몽", "청포도", "유자", "제로콜라"],
            "브랜드": ["코카콜라", "펩시", "칠성사이다", "환타"]
        },
        "과일주스": {
            "플레이버": ["오렌지", "사과", "망고", "포도", "타트체리", "자몽"],
            "브랜드": ["델몬트", "썬키스트", "따옴", "돈시몬"]
        }
    }

    selected_group = st.selectbox("📂 분석계열", list(beverage_structure.keys()))

    # 플레이버
    col1, col2 = st.columns([2, 1])
    with col1:
        flavor_select = st.selectbox("추천 플레이버", beverage_structure[selected_group]["플레이버"])
    with col2:
        flavor_custom = st.text_input("직접입력(플레이버)")

    final_flavor = flavor_custom if flavor_custom else flavor_select

    # 브랜드
    col3, col4 = st.columns([2, 1])
    with col3:
        brand_select = st.selectbox("추천 브랜드", beverage_structure[selected_group]["브랜드"])
    with col4:
        brand_custom = st.text_input("직접입력(브랜드)")

    final_brand = brand_custom if brand_custom else brand_select

    if st.button("📊 전략 분석 실행"):

        if not final_flavor and not final_brand:
            st.warning("⚠ 플레이버 또는 브랜드를 선택해야 쇼핑 데이터가 출력됩니다.")
            return

        # ============================================================
        # 네이버 쇼핑 API 공통 함수
        # ============================================================
        def fetch_shopping(keyword, display=100):
            enc = urllib.parse.quote(keyword)
            res = requests.get(
                f"https://openapi.naver.com/v1/search/shop.json?query={enc}&display={display}",
                headers={
                    "X-Naver-Client-Id": st.secrets["naver_shopping"]["NAVER_CLIENT_ID"],
                    "X-Naver-Client-Secret": st.secrets["naver_shopping"]["NAVER_CLIENT_SECRET"],
                }
            )
            if res.status_code != 200:
                st.error(f"API 오류: {res.text}")
                return None
            items = res.json().get("items", [])
            if not items:
                return None
            df = pd.DataFrame(items)
            df["lprice"] = pd.to_numeric(df["lprice"], errors="coerce")
            return df

        # ============================================================
        # 1) 선택한 브랜드 + 플레이버 검색
        # ============================================================
        search_keyword = f"{final_brand} {final_flavor}"
        df_shop = fetch_shopping(search_keyword)

        if df_shop is None:
            st.warning("쇼핑 데이터를 불러오지 못했습니다.")
            return

        # ============================================================
        # 2) 건강기능성음료 선택 시 → 기능성 음료 시장 전체 추가 검색
        # ============================================================
        df_functional = None
        flavor_counts = {}
        brand_counts = {}

        if selected_group == "건강기능성음료":
            st.info("🔍 기능성 음료 시장 전체 데이터를 추가로 검색합니다...")
            df_functional = fetch_shopping("기능성 음료", display=100)

        # ============================================================
        # 지표 계산 (선택 브랜드+플레이버 기준)
        # ============================================================
        brand_share = df_shop["brand"].value_counts(normalize=True) * 100
        dominance_index = brand_share.iloc[0] * len(df_shop)
        avg_price = df_shop["lprice"].mean()
        premium_threshold = df_shop["lprice"].median()

        df_shop["price_position"] = df_shop["lprice"].apply(
            lambda x: "프리미엄" if x > premium_threshold else "가성비"
        )

        opportunity_score = (100 - brand_share.iloc[0]) * (1 if avg_price < premium_threshold else 0.8)

        if opportunity_score > 50:
            strategy_grade = "A"
        elif opportunity_score > 30:
            strategy_grade = "B"
        else:
            strategy_grade = "C"

        # ============================================================
        # 카드뉴스 출력 (브랜드+플레이버)
        # ============================================================
        st.markdown(f"### 📰 전략 카드뉴스 — `{search_keyword}`")

        colA, colB = st.columns(2)
        with colA:
            st.markdown("#### 🏷 브랜드 점유율")
            st.bar_chart(brand_share)
        with colB:
            st.markdown("#### 💰 평균가격")
            st.metric("평균가", f"{avg_price:,.0f} 원")

        colC, colD = st.columns(2)
        with colC:
            st.markdown("#### 📊 프리미엄 vs 가성비")
            st.bar_chart(df_shop["price_position"].value_counts())
        with colD:
            st.markdown("#### 🧮 브랜드 지배력 지수")
            st.metric("지배력지수", f"{dominance_index:.1f}")

        st.markdown("### 🚀 신규 진입 기회 점수")
        st.metric("Opportunity Score", f"{opportunity_score:.1f}")
        st.metric("전략 등급", strategy_grade)

        # ============================================================
        # 기능성음료 시장 현황 (건강기능성음료 선택 시만 표시)
        # ============================================================
        if df_functional is not None:
            st.markdown("---")
            st.markdown("### 🏥 기능성 음료 시장 전체 현황")

            func_brand_share = df_functional["brand"].value_counts(normalize=True) * 100
            func_avg_price = df_functional["lprice"].mean()
            func_premium_threshold = df_functional["lprice"].median()
            df_functional["price_position"] = df_functional["lprice"].apply(
                lambda x: "프리미엄" if x > func_premium_threshold else "가성비"
            )

            col_f1, col_f2 = st.columns(2)
            with col_f1:
                st.markdown("#### 🏷 기능성음료 브랜드 점유율 TOP10")
                st.bar_chart(func_brand_share.head(10))
            with col_f2:
                st.markdown("#### 💰 기능성음료 평균가격")
                st.metric("평균가", f"{func_avg_price:,.0f} 원")
                st.markdown("#### 📊 프리미엄 vs 가성비")
                st.bar_chart(df_functional["price_position"].value_counts())

            # 플레이버별 시장 노출 비교
            st.markdown("#### 🍹 플레이버별 시장 노출 비교 (기능성음료)")
            for flv in beverage_structure["건강기능성음료"]["플레이버"]:
                flavor_counts[flv] = df_functional["title"].str.contains(flv, na=False).sum()
            flavor_series = pd.Series(flavor_counts).sort_values(ascending=False)
            st.bar_chart(flavor_series)

            # 브랜드별 시장 노출 비교
            st.markdown("#### 🏢 브랜드별 시장 노출 비교 (기능성음료)")
            for br in beverage_structure["건강기능성음료"]["브랜드"]:
                brand_counts[br] = df_functional["title"].str.contains(br, na=False, case=False).sum()
            brand_series = pd.Series(brand_counts).sort_values(ascending=False)
            st.bar_chart(brand_series)

        # ============================================================
        # AI 전략 보고서
        # ============================================================
        try:
            openai_enabled = (
                "openai" in st.secrets
                and bool(st.secrets["openai"].get("OPENAI_API_KEY"))
                and OpenAI is not None
            )
        except Exception:
            openai_enabled = False

        if openai_enabled:
            client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])

            with st.spinner("AI 전략 보고서 생성 중..."):

                # 기능성음료 추가 컨텍스트
                functional_context = ""
                if df_functional is not None:
                    func_brand_top5 = func_brand_share.head(5).to_dict()
                    functional_context = f"""
                    [기능성 음료 시장 전체 현황]
                    - 시장 평균가격: {func_avg_price:,.0f}원
                    - 브랜드 점유율 TOP5: {func_brand_top5}
                    - 플레이버 노출 수: {flavor_counts}
                    - 브랜드 노출 수: {brand_counts}
                    """

                prompt = f"""
                [분석 대상]
                계열: {selected_group}
                브랜드: {final_brand}, 플레이버: {final_flavor}

                [쇼핑 검색 데이터]
                - 브랜드 점유율: {brand_share.to_dict()}
                - 평균가격: {avg_price:,.0f}원
                - 브랜드 지배력 지수: {dominance_index:.1f}
                - 신규진입 기회점수: {opportunity_score:.1f}
                - 전략 등급: {strategy_grade}

                {functional_context}

                위 데이터를 기반으로 아래 항목을 포함한 통합 전략 보고서를 작성하세요:
                1. 시장 경쟁 구조 분석
                2. 가격 포지셔닝 전략
                3. 유망 플레이버 방향
                4. 신규 진입 전략 및 리스크
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                )

            report_text = response.choices[0].message.content

            # 전문 리포트 스타일 출력
            st.markdown("""
            <style>
            .ai-report-container {
                background: #0E1117;
                padding: 30px;
                border-radius: 14px;
                margin-top: 25px;
                border: 1px solid #1F2937;
                box-shadow: 0 6px 18px rgba(0,0,0,0.4);
                font-family: 'Segoe UI', 'Roboto', sans-serif;
            }
            .ai-report-title {
                font-size: 20px;
                font-weight: 700;
                color: #FFFFFF;
                display: flex;
                align-items: center;
                gap: 10px;
                margin-bottom: 8px;
            }
            .ai-model-label {
                font-size: 13px;
                color: #9CA3AF;
                margin-bottom: 20px;
            }
            .ai-report-body {
                font-size: 15px;
                line-height: 1.8;
                color: #F3F4F6;
                white-space: pre-wrap;
            }
            </style>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="ai-report-container">
                <div class="ai-report-title">
                    📊 <span>AI 통합 전략 보고서</span>
                </div>
                <div class="ai-model-label">
                    🤖 모델: <strong>gpt-4o-mini</strong>
                </div>
                <div class="ai-report-body">
                    {report_text}
                </div>
            </div>
            """, unsafe_allow_html=True)

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

        else:
            st.info("OpenAI 키가 없어 AI 보고서는 비활성화됩니다.")
