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

    # ============================================================
    # part_A 전용 보조 스타일 (main_app.py CSS와 충돌 없는 것만)
    # ============================================================
    st.markdown("""
    <style>
    .section-title {
        font-size: 15px;
        font-weight: 700;
        color: #00C8D4;
        border-left: 4px solid #00C8D4;
        padding-left: 10px;
        margin: 20px 0 12px;
    }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        margin: 2px;
    }
    .badge-blue   { background: #1e40af; color: #bfdbfe; }
    .badge-green  { background: #14532d; color: #bbf7d0; }
    .badge-yellow { background: #713f12; color: #fef08a; }
    .badge-red    { background: #7f1d1d; color: #fecaca; }
    .risk-row {
        background: #1A2E4A;
        border-left: 4px solid #ef4444;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .risk-row.medium { border-left-color: #f59e0b; }
    .risk-row.low    { border-left-color: #22c55e; }
    .plan-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        color: #E8F0FE;
    }
    .plan-table th {
        background: #0B1629;
        color: #7A9CC0;
        padding: 10px 14px;
        text-align: left;
        font-weight: 600;
        border-bottom: 1px solid #1E3A5A;
    }
    .plan-table td {
        padding: 10px 14px;
        border-bottom: 1px solid #1A2E4A;
    }
    .plan-table tr:hover td { background: #1A2E4A; }
    .ai-box {
        background: #0B1629;
        border: 1px solid #00C8D4;
        border-radius: 12px;
        padding: 20px 24px;
        margin-top: 16px;
        line-height: 1.8;
        font-size: 14px;
        color: #E8F0FE;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

    # ============================================================
    # 페이지 타이틀
    # ============================================================
    st.markdown("## 🧪 신제품개발시스템")
    st.caption("시장 정보 분석부터 개발보고서까지 신제품 개발 전 과정을 지원합니다.")
    st.markdown("---")

    # ============================================================
    # KPI 요약
    # ============================================================
    k1, k2, k3, k4 = st.columns(4)
    for col, label, value in [
        (k1, "📈 진행 중 프로젝트", "147"),
        (k2, "🧬 배합비 개발 중",   "32"),
        (k3, "⚠️ 리스크 항목",      "5"),
        (k4, "📋 완료 보고서",       "89"),
    ]:
        col.metric(label, value)

    st.markdown("<br>", unsafe_allow_html=True)

    # ============================================================
    # 공통 DB
    # ============================================================
    beverage_structure = {
        "건강기능성음료": {
            "플레이버": ["망고", "베리", "레몬", "복숭아", "초코"],
            "브랜드":   ["몬스터", "레드불", "셀시어스", "마이밀", "닥터유"]
        },
        "탄산음료": {
            "플레이버": ["콜라", "레몬", "자몽", "라임", "청포도"],
            "브랜드":   ["코카콜라", "펩시", "칠성사이다", "환타"]
        },
        "과일주스": {
            "플레이버": ["오렌지", "사과", "망고", "포도", "타트체리"],
            "브랜드":   ["델몬트", "썬키스트", "따옴", "돈시몬"]
        },
        "전통/차음료": {
            "플레이버": ["녹차", "홍차", "보리차", "식혜", "쌍화차"],
            "브랜드":   ["동서", "광동", "웅진"]
        },
        "제로/저당음료": {
            "플레이버": ["제로콜라", "제로사이다", "무가당레몬"],
            "브랜드":   ["코카콜라제로", "펩시제로", "칠성제로"]
        }
    }

    # OpenAI 활성화 여부
    try:
        openai_enabled = (
            "openai" in st.secrets
            and bool(st.secrets["openai"].get("OPENAI_API_KEY"))
            and OpenAI is not None
        )
    except Exception:
        openai_enabled = False

    # 공통 선택 위젯 함수
    def flavor_brand_selector(group_key, tab_key):
        """계열별 플레이버/브랜드 선택 + 없음/직접입력 UI"""
        selected_group = st.selectbox(
            "📂 분석 계열",
            list(beverage_structure.keys()),
            key=f"{tab_key}_group"
        )
        flavors_list = ["없음"] + beverage_structure[selected_group]["플레이버"]
        brands_list  = ["없음"] + beverage_structure[selected_group]["브랜드"]

        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            f_sel = st.selectbox("추천 플레이버", flavors_list, key=f"{tab_key}_fsel")
        with col_f2:
            f_cus = st.text_input("직접입력(플레이버)", key=f"{tab_key}_fcus", placeholder="없음 선택 후 입력")
        final_flavor = f_cus.strip() if f_cus.strip() else (f_sel if f_sel != "없음" else "")

        col_b1, col_b2 = st.columns([2, 1])
        with col_b1:
            b_sel = st.selectbox("추천 브랜드", brands_list, key=f"{tab_key}_bsel")
        with col_b2:
            b_cus = st.text_input("직접입력(브랜드)", key=f"{tab_key}_bcus", placeholder="없음 선택 후 입력")
        final_brand = b_cus.strip() if b_cus.strip() else (b_sel if b_sel != "없음" else "")

        return selected_group, final_flavor, final_brand

    # ============================================================
    # 탭
    # ============================================================
    tabs = st.tabs([
        "📈 시장정보분석",
        "🧬 배합비개발",
        "⚠️ 공정리스크확인",
        "📋 생산계획서",
        "📝 개발보고서"
    ])

    # ============================================================
    # 📈 탭 0: 시장정보분석
    # ============================================================
    with tabs[0]:

        st.markdown('<div class="section-title">음료 시장 트렌드 & 쇼핑 분석</div>', unsafe_allow_html=True)

        if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
            st.error("네이버 API secrets가 설정되지 않았습니다.")
            return

        selected_group0, final_flavor0, final_brand0 = flavor_brand_selector("", "tab0")

        col_c, col_d, col_e = st.columns(3)
        with col_c:
            start_date = st.date_input("시작일", date(2023, 1, 1))
        with col_d:
            end_date = st.date_input("종료일", date.today())
        with col_e:
            time_unit = st.selectbox("📅 분석 단위", ["month", "week", "date"])

        if st.button("📊 분석 실행", key="market_run"):

            search_parts = [p for p in [final_brand0, final_flavor0] if p]
            if not search_parts:
                st.warning("⚠️ 플레이버 또는 브랜드 중 하나 이상을 선택하거나 입력하세요.")
                return
            search_keyword = " ".join(search_parts)

            # DataLab 트렌드
            beverage_groups_datalab = {
                "건강기능성음료": ["에너지음료", "비타민음료", "단백질음료", "기능성음료"],
                "탄산음료":       ["콜라", "사이다", "이온음료", "과즙탄산음료"],
                "과일주스":       ["오렌지주스", "사과주스", "망고주스", "레몬주스"],
                "전통/차음료":    ["식혜", "녹차음료", "홍차음료", "보리차"],
                "제로/저당음료":  ["제로음료", "저당음료", "무설탕음료"],
            }

            body = {
                "startDate": start_date.strftime("%Y-%m-%d"),
                "endDate":   end_date.strftime("%Y-%m-%d"),
                "timeUnit":  time_unit,
                "keywordGroups": [{
                    "groupName": selected_group0,
                    "keywords":  beverage_groups_datalab.get(selected_group0, [search_keyword])
                }],
            }
            response = requests.post(
                "https://openapi.naver.com/v1/datalab/search",
                headers={
                    "X-Naver-Client-Id":     st.secrets["naver_search"]["NAVER_CLIENT_ID"],
                    "X-Naver-Client-Secret": st.secrets["naver_search"]["NAVER_CLIENT_SECRET"],
                    "Content-Type": "application/json",
                },
                data=json.dumps(body),
            )

            trend_summary = {}
            if response.status_code == 200:
                result = response.json()
                if "results" in result:
                    st.markdown('<div class="section-title">📉 검색 트렌드</div>', unsafe_allow_html=True)
                    df_trend = pd.DataFrame(result["results"][0]["data"])
                    df_trend["period"] = pd.to_datetime(df_trend["period"])
                    trend_summary[selected_group0] = df_trend["ratio"].tolist()[-3:]

                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=df_trend["period"], y=df_trend["ratio"],
                        mode="lines+markers", name=selected_group0,
                        line=dict(color="#00C8D4", width=2), marker=dict(size=5)
                    ))
                    fig.update_layout(
                        paper_bgcolor="#0B1629", plot_bgcolor="#0B1629",
                        font=dict(color="#7A9CC0"),
                        title=dict(text=f"{selected_group0} 트렌드", font=dict(color="#E8F0FE")),
                        hovermode="x unified",
                        xaxis=dict(gridcolor="#1A2E4A"),
                        yaxis=dict(gridcolor="#1A2E4A"),
                    )
                    st.plotly_chart(fig, use_container_width=True)

            # 쇼핑 분석
            shopping_summary = {}
            enc = urllib.parse.quote(search_keyword)
            shop_response = requests.get(
                f"https://openapi.naver.com/v1/search/shop.json?query={enc}&display=100",
                headers={
                    "X-Naver-Client-Id":     st.secrets["naver_shopping"]["NAVER_CLIENT_ID"],
                    "X-Naver-Client-Secret": st.secrets["naver_shopping"]["NAVER_CLIENT_SECRET"],
                },
            )

            if shop_response.status_code == 200:
                items = shop_response.json().get("items", [])
                if items:
                    df_shop = pd.DataFrame(items)
                    df_shop["lprice"] = pd.to_numeric(df_shop["lprice"], errors="coerce")

                    st.markdown(f'<div class="section-title">🛍 쇼핑 현황 — "{search_keyword}"</div>', unsafe_allow_html=True)

                    m1, m2, m3 = st.columns(3)
                    m1.metric("평균 가격", f"{df_shop['lprice'].mean():,.0f} 원")
                    m2.metric("최저 가격", f"{df_shop['lprice'].min():,.0f} 원")
                    m3.metric("상품 수",   f"{len(df_shop):,} 개")

                    st.dataframe(
                        df_shop[["title", "lprice", "brand", "mallName"]].rename(columns={
                            "title": "상품명", "lprice": "최저가", "brand": "브랜드", "mallName": "쇼핑몰"
                        }),
                        use_container_width=True, height=220
                    )

                    brand_rank = df_shop["brand"].value_counts().reset_index()
                    brand_rank.columns = ["브랜드", "노출건수"]

                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        st.markdown('<div class="section-title">🏆 브랜드 노출 순위</div>', unsafe_allow_html=True)
                        st.bar_chart(brand_rank.set_index("브랜드")["노출건수"])
                    with col_b2:
                        st.markdown('<div class="section-title">💰 브랜드 평균 가격</div>', unsafe_allow_html=True)
                        st.bar_chart(df_shop.groupby("brand")["lprice"].mean().sort_values(ascending=False))

                    shopping_summary = {
                        "평균가격": float(df_shop["lprice"].mean()),
                        "브랜드순위": brand_rank.to_dict(),
                    }
                else:
                    st.info("쇼핑 검색 결과가 없습니다.")

            # AI 보고서
            if openai_enabled:
                st.markdown('<div class="section-title">🤖 AI 통합 전략 보고서</div>', unsafe_allow_html=True)
                with st.spinner("AI 분석 중..."):
                    client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])
                    prompt = f"""
                    검색 키워드: {search_keyword}
                    트렌드 데이터: {trend_summary}
                    쇼핑 데이터: {shopping_summary}
                    위 내용을 기반으로 시장 성장성, 브랜드 경쟁 구조, 가격 전략, 신규 진입 전략을 종합 보고서로 작성하세요.
                    """
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                    )
                st.markdown(f'<div class="ai-box">{resp.choices[0].message.content}</div>', unsafe_allow_html=True)
            else:
                st.info("OpenAI 키가 없어 AI 보고서는 비활성화됩니다.")

    # ============================================================
    # 🧬 탭 1: 배합비개발
    # ============================================================
    with tabs[1]:

        st.markdown('<div class="section-title">배합비 설계 & 원료 구성</div>', unsafe_allow_html=True)

        selected_group1, final_flavor1, final_brand1 = flavor_brand_selector("", "tab1")
        product_name1 = f"{final_brand1} {final_flavor1}".strip() or "미입력"

        col1, col2 = st.columns(2)
        with col1:
            target_brix = st.slider("🍬 목표 당도 (Brix)", 0.0, 20.0, 10.0, 0.5)
            target_ph   = st.slider("🧪 목표 pH", 2.0, 7.0, 3.5, 0.1)
        with col2:
            target_cost = st.number_input("💰 목표 원가 (원/L)", min_value=0, value=500, step=10)
            memo        = st.text_area("📝 특이사항", placeholder="특수 원료, 알레르기 주의사항 등", height=82)

        st.markdown('<div class="section-title">원료 구성표</div>', unsafe_allow_html=True)

        ingredient_df = pd.DataFrame({
            "원료명":      ["정제수", "설탕", "구연산", "향료", "비타민C"],
            "규격":        ["식품용", "백설탕", "무수", "천연", "L-아스코르브산"],
            "함량(%)":    [85.0, 8.0, 0.3, 0.2, 0.05],
            "원가(원/kg)": [10, 800, 2000, 15000, 30000],
            "비고":        ["기본", "감미", "산미", "향", "기능성"],
        })

        edited_df = st.data_editor(
            ingredient_df,
            use_container_width=True,
            num_rows="dynamic",
            key="ingredient_editor"
        )

        total_ratio    = edited_df["함량(%)"].sum()
        estimated_cost = (edited_df["함량(%)"] / 100 * edited_df["원가(원/kg)"]).sum() * 10

        s1, s2, s3 = st.columns(3)
        s1.metric("총 함량 합계", f"{total_ratio:.2f} %",
                  delta=f"{total_ratio - 100:.2f}%" if abs(total_ratio - 100) > 0.01 else "정상")
        s2.metric("예상 원가", f"{estimated_cost:,.0f} 원/L")
        s3.metric("목표 대비", f"{estimated_cost - target_cost:+,.0f} 원", delta_color="inverse")

        if st.button("🧬 배합비 AI 최적화 제안", key="formula_ai"):
            if openai_enabled:
                client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])
                with st.spinner("AI 배합비 분석 중..."):
                    prompt = f"""
                    제품명: {product_name1}, 계열: {selected_group1}
                    플레이버: {final_flavor1}, 브랜드: {final_brand1}
                    목표 당도: {target_brix} Brix, 목표 pH: {target_ph}, 목표 원가: {target_cost}원/L
                    현재 원료구성: {edited_df.to_dict()}
                    원가 절감, 관능 개선, 규격 충족 측면에서 개선 방향을 제안하세요.
                    """
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                    )
                st.markdown(f'<div class="ai-box">{resp.choices[0].message.content}</div>', unsafe_allow_html=True)
            else:
                st.info("OpenAI 키가 없어 AI 제안은 비활성화됩니다.")

    # ============================================================
    # ⚠️ 탭 2: 공정리스크확인
    # ============================================================
    with tabs[2]:

        st.markdown('<div class="section-title">공정 단계별 리스크 점검</div>', unsafe_allow_html=True)

        process_step = st.selectbox(
            "🏭 공정 단계 선택",
            ["전체", "원료 입고", "전처리/용해", "배합", "살균", "충전", "포장", "출하"]
        )

        risk_data = [
            {"단계": "원료 입고", "항목": "원료 규격 미달",      "등급": "high",   "조치": "COA 확인 및 반품 절차 진행"},
            {"단계": "원료 입고", "항목": "이물 혼입 가능성",    "등급": "medium", "조치": "입고 검사 강화 (금속 검출기)"},
            {"단계": "배합",      "항목": "당도 편차 ±0.5 초과", "등급": "medium", "조치": "자동 계량 시스템 점검"},
            {"단계": "살균",      "항목": "살균 온도 미달",       "등급": "high",   "조치": "온도 센서 교체 및 재살균"},
            {"단계": "충전",      "항목": "충전량 편차",          "등급": "low",    "조치": "충전기 노즐 청소"},
            {"단계": "포장",      "항목": "라벨 오부착",          "등급": "low",    "조치": "비전 검사 시스템 운영"},
            {"단계": "출하",      "항목": "유통기한 오기재",      "등급": "high",   "조치": "최종 출하 검사 체크리스트 확인"},
        ]

        filtered = risk_data if process_step == "전체" else [r for r in risk_data if r["단계"] == process_step]

        high_cnt   = sum(1 for r in filtered if r["등급"] == "high")
        medium_cnt = sum(1 for r in filtered if r["등급"] == "medium")
        low_cnt    = sum(1 for r in filtered if r["등급"] == "low")

        r1, r2, r3 = st.columns(3)
        r1.metric("🔴 긴급", f"{high_cnt} 건")
        r2.metric("🟡 주의", f"{medium_cnt} 건")
        r3.metric("🟢 일반", f"{low_cnt} 건")

        st.markdown("<br>", unsafe_allow_html=True)

        grade_map = {
            "high":   ("🔴 긴급", "badge-red",    "risk-row"),
            "medium": ("🟡 주의", "badge-yellow", "risk-row medium"),
            "low":    ("🟢 일반", "badge-green",  "risk-row low"),
        }

        for item in filtered:
            label, badge_cls, row_cls = grade_map[item["등급"]]
            st.markdown(f"""
            <div class="{row_cls}">
                <div>
                    <span class="badge {badge_cls}">{label}</span>
                    &nbsp;<strong style="color:#E8F0FE">[{item['단계']}]</strong>
                    &nbsp;<span style="color:#7A9CC0">{item['항목']}</span>
                </div>
                <div style="font-size:12px;color:#7A9CC0;max-width:50%;text-align:right;">
                    💡 {item['조치']}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">리스크 신규 등록</div>', unsafe_allow_html=True)
        col_n1, col_n2 = st.columns(2)
        with col_n1:
            new_step   = st.selectbox("공정 단계", ["원료 입고", "전처리/용해", "배합", "살균", "충전", "포장", "출하"], key="new_step")
            new_item   = st.text_input("리스크 항목")
        with col_n2:
            new_grade  = st.selectbox("등급", ["high", "medium", "low"], key="new_grade")
            new_action = st.text_input("조치 방안")

        if st.button("➕ 리스크 등록", key="add_risk"):
            if new_item:
                st.success(f"✅ [{new_step}] '{new_item}' 리스크가 등록되었습니다.")
            else:
                st.warning("리스크 항목을 입력하세요.")

    # ============================================================
    # 📋 탭 3: 생산계획서
    # ============================================================
    with tabs[3]:

        st.markdown('<div class="section-title">생산 계획 수립</div>', unsafe_allow_html=True)

        selected_group3, final_flavor3, final_brand3 = flavor_brand_selector("", "tab3")
        plan_product = f"{final_brand3} {final_flavor3}".strip() or "미입력"

        col_p1, col_p2, col_p3 = st.columns(3)
        with col_p1:
            plan_line = st.selectbox("생산 라인", ["1라인", "2라인", "3라인", "다목적 라인"])
        with col_p2:
            plan_start = st.date_input("생산 시작일", key="plan_start")
            plan_end   = st.date_input("생산 종료일", key="plan_end")
        with col_p3:
            plan_qty  = st.number_input("생산 수량 (개)", min_value=0, value=10000, step=500)
            plan_unit = st.selectbox("용량", ["200mL", "250mL", "355mL", "500mL", "1L", "1.5L"])

        volume_map   = {"200mL": 0.2, "250mL": 0.25, "355mL": 0.355, "500mL": 0.5, "1L": 1.0, "1.5L": 1.5}
        total_volume = plan_qty * volume_map.get(plan_unit, 0.5)

        st.markdown(f'<div class="section-title">📦 [{plan_product}] 원부자재 소요량</div>', unsafe_allow_html=True)

        mat_df = pd.DataFrame({
            "원부자재": ["정제수", "설탕", "구연산", "향료", "용기", "캡", "라벨"],
            "단위":     ["L", "kg", "kg", "kg", "개", "개", "개"],
            "소요량":   [
                round(total_volume * 0.85, 1),
                round(total_volume * 0.08, 2),
                round(total_volume * 0.003, 3),
                round(total_volume * 0.002, 3),
                plan_qty, plan_qty, plan_qty,
            ],
            "재고 현황": ["충분", "충분", "부족", "충분", "충분", "확인 필요", "충분"],
        })

        def highlight_stock(val):
            if val == "부족":
                return "background-color:#7f1d1d;color:#fecaca"
            elif val == "확인 필요":
                return "background-color:#713f12;color:#fef08a"
            return ""

        st.dataframe(mat_df.style.applymap(highlight_stock, subset=["재고 현황"]), use_container_width=True)

        p1, p2, p3 = st.columns(3)
        p1.metric("총 생산량", f"{plan_qty:,} 개")
        p2.metric("총 용량",   f"{total_volume:,.0f} L")
        days = max((plan_end - plan_start).days, 1)
        p3.metric("일 평균 생산", f"{plan_qty // days:,} 개/일")

        st.markdown('<div class="section-title">생산 일정표</div>', unsafe_allow_html=True)
        schedule = [
            ("원료 입고 확인",  "원료팀",  "완료"),
            ("설비 세팅 & CIP", "생산팀",  "완료"),
            ("시험 생산",       "QC팀",    "진행 중"),
            ("본 생산",         "생산팀",  "대기"),
            ("품질 검사",       "QC팀",    "대기"),
            ("출하",            "물류팀",  "대기"),
        ]
        badge_map2 = {"완료": "badge-green", "진행 중": "badge-yellow", "대기": "badge-blue"}
        rows_html  = "".join(
            f"<tr><td>{s[0]}</td><td>{s[1]}</td>"
            f"<td><span class='badge {badge_map2[s[2]]}'>{s[2]}</span></td></tr>"
            for s in schedule
        )
        st.markdown(f"""
        <table class="plan-table">
          <tr><th>단계</th><th>담당</th><th>상태</th></tr>
          {rows_html}
        </table>
        """, unsafe_allow_html=True)

    # ============================================================
    # 📝 탭 4: 개발보고서
    # ============================================================
    with tabs[4]:

        st.markdown('<div class="section-title">개발보고서 작성</div>', unsafe_allow_html=True)

        selected_group4, final_flavor4, final_brand4 = flavor_brand_selector("", "tab4")
        rep_product = f"{final_brand4} {final_flavor4}".strip() or "미입력"

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            rep_manager = st.text_input("담당자", placeholder="홍길동")
            rep_date    = st.date_input("보고서 작성일", date.today())
        with col_r2:
            rep_version = st.selectbox("버전", ["v1.0", "v1.1", "v2.0", "최종"])
            rep_status  = st.selectbox("진행 상태", ["개발 중", "시험 생산", "승인 대기", "완료"])

        st.markdown('<div class="section-title">개발 내용</div>', unsafe_allow_html=True)

        rep_concept = st.text_area("📌 제품 컨셉 & 개발 배경", height=80, placeholder="소비자 트렌드, 개발 목적 등")
        rep_formula = st.text_area("🧬 배합비 요약", height=80, placeholder="주요 원료 및 함량 요약")
        rep_sensory = st.text_area("👅 관능 평가 결과", height=80, placeholder="색상, 향, 맛, 전체적 기호도 등")
        rep_quality = st.text_area("🔬 품질 규격", height=80, placeholder="당도, pH, 미생물, 이화학 규격 등")
        rep_issue   = st.text_area("⚠️ 이슈 & 개선사항", height=80, placeholder="발생 이슈 및 해결 방안")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🤖 AI 보고서 초안 생성", key="report_ai"):
                if openai_enabled:
                    client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])
                    with st.spinner("AI 보고서 작성 중..."):
                        prompt = f"""
                        제품명: {rep_product}, 계열: {selected_group4}
                        플레이버: {final_flavor4}, 브랜드: {final_brand4}
                        담당자: {rep_manager}, 버전: {rep_version}
                        컨셉: {rep_concept}
                        배합비: {rep_formula}
                        관능평가: {rep_sensory}
                        품질규격: {rep_quality}
                        이슈: {rep_issue}
                        위 내용을 바탕으로 신제품 개발 보고서를 전문적으로 작성하세요.
                        항목: 개발배경, 제품특성, 배합비 요약, 관능평가, 품질기준, 향후 과제
                        """
                        resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[{"role": "user", "content": prompt}],
                        )
                    st.session_state["report_ai_text"] = resp.choices[0].message.content
                else:
                    st.info("OpenAI 키가 없어 AI 초안 생성은 비활성화됩니다.")

        with col_btn2:
            if st.button("💾 보고서 저장", key="report_save"):
                st.success(f"✅ [{rep_product}] {rep_version} 보고서가 저장되었습니다.")

        if "report_ai_text" in st.session_state:
            st.markdown('<div class="section-title">📄 AI 생성 보고서</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="ai-box">{st.session_state["report_ai_text"]}</div>',
                unsafe_allow_html=True
            )

        st.markdown('<div class="section-title">📁 최근 보고서 목록</div>', unsafe_allow_html=True)
        history = pd.DataFrame({
            "제품명":  ["몬스터 망고", "코카콜라 제로", "홍차 라떼", "델몬트 타트체리", "닥터유 베리"],
            "버전":    ["v2.0", "최종", "v1.1", "최종", "v1.0"],
            "담당자":  ["김개발", "이연구", "박기획", "최분석", "정연구"],
            "작성일":  ["2025-01-15", "2025-01-10", "2024-12-20", "2024-12-05", "2024-11-28"],
            "상태":    ["승인 대기", "완료", "완료", "완료", "개발 중"],
        })
        st.dataframe(history, use_container_width=True)
