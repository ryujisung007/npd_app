import streamlit as st
import pandas as pd
from datetime import date

BEVERAGE_STRUCTURE = {
    "건강기능성음료": {"플레이버": ["망고", "베리", "레몬", "복숭아", "초코"], "브랜드": ["몬스터", "레드불", "셀시어스", "마이밀", "닥터유"]},
    "탄산음료":       {"플레이버": ["콜라", "레몬", "자몽", "라임", "청포도"], "브랜드": ["코카콜라", "펩시", "칠성사이다", "환타"]},
    "과일주스":       {"플레이버": ["오렌지", "사과", "망고", "포도", "타트체리"], "브랜드": ["델몬트", "썬키스트", "따옴", "돈시몬"]},
    "전통/차음료":    {"플레이버": ["녹차", "홍차", "보리차", "식혜", "쌍화차"], "브랜드": ["동서", "광동", "웅진"]},
    "제로/저당음료":  {"플레이버": ["제로콜라", "제로사이다", "무가당레몬"], "브랜드": ["코카콜라제로", "펩시제로", "칠성제로"]},
}


def run():
    st.markdown("""
    <style>
    .section-title {
        font-size: 15px; font-weight: 700; color: #00C8D4;
        border-left: 4px solid #00C8D4; padding-left: 10px; margin: 20px 0 12px;
    }
    .badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:11px; font-weight:700; margin:2px; }
    .badge-blue   { background:#1e40af; color:#bfdbfe; }
    .badge-green  { background:#14532d; color:#bbf7d0; }
    .badge-yellow { background:#713f12; color:#fef08a; }
    .plan-table { width:100%; border-collapse:collapse; font-size:13px; color:#E8F0FE; }
    .plan-table th { background:#0B1629; color:#7A9CC0; padding:10px 14px; text-align:left; font-weight:600; border-bottom:1px solid #1E3A5A; }
    .plan-table td { padding:10px 14px; border-bottom:1px solid #1A2E4A; }
    .plan-table tr:hover td { background:#1A2E4A; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">생산 계획 수립</div>', unsafe_allow_html=True)

    # 계열/플레이버/브랜드 선택
    selected_group = st.selectbox("📂 제품 계열", list(BEVERAGE_STRUCTURE.keys()), key="plan_group")
    flavors_list   = ["없음"] + BEVERAGE_STRUCTURE[selected_group]["플레이버"]
    brands_list    = ["없음"] + BEVERAGE_STRUCTURE[selected_group]["브랜드"]

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        f_sel = st.selectbox("🍊 플레이버", flavors_list, key="plan_fsel")
        f_cus = st.text_input("직접입력(플레이버)", key="plan_fcus", placeholder="없음 선택 후 입력")
        final_flavor = f_cus.strip() if f_cus.strip() else (f_sel if f_sel != "없음" else "")
    with col_s2:
        b_sel = st.selectbox("🏷 브랜드", brands_list, key="plan_bsel")
        b_cus = st.text_input("직접입력(브랜드)", key="plan_bcus", placeholder="없음 선택 후 입력")
        final_brand = b_cus.strip() if b_cus.strip() else (b_sel if b_sel != "없음" else "")

    plan_product = f"{final_brand} {final_flavor}".strip() or "미입력"

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        plan_line = st.selectbox("생산 라인", ["1라인", "2라인", "3라인", "다목적 라인"], key="plan_line")
    with col_p2:
        plan_start = st.date_input("생산 시작일", key="plan_start")
        plan_end   = st.date_input("생산 종료일", key="plan_end")
    with col_p3:
        plan_qty  = st.number_input("생산 수량 (개)", min_value=0, value=10000, step=500, key="plan_qty")
        plan_unit = st.selectbox("용량", ["200mL", "250mL", "355mL", "500mL", "1L", "1.5L"], key="plan_unit")

    volume_map   = {"200mL": 0.2, "250mL": 0.25, "355mL": 0.355, "500mL": 0.5, "1L": 1.0, "1.5L": 1.5}
    total_volume = plan_qty * volume_map.get(plan_unit, 0.5)

    st.markdown(f'<div class="section-title">📦 [{plan_product}] 원부자재 소요량</div>', unsafe_allow_html=True)

    mat_df = pd.DataFrame({
        "원부자재": ["정제수", "설탕", "구연산", "향료", "용기", "캡", "라벨"],
        "단위":     ["L", "kg", "kg", "kg", "개", "개", "개"],
        "소요량":   [
            round(total_volume * 0.85, 1), round(total_volume * 0.08, 2),
            round(total_volume * 0.003, 3), round(total_volume * 0.002, 3),
            plan_qty, plan_qty, plan_qty,
        ],
        "재고 현황": ["충분", "충분", "부족", "충분", "충분", "확인 필요", "충분"],
    })

    def highlight_stock(val):
        if val == "부족":        return "background-color:#7f1d1d;color:#fecaca"
        elif val == "확인 필요": return "background-color:#713f12;color:#fef08a"
        return ""

    st.dataframe(mat_df.style.applymap(highlight_stock, subset=["재고 현황"]), use_container_width=True)

    p1, p2, p3 = st.columns(3)
    p1.metric("총 생산량",    f"{plan_qty:,} 개")
    p2.metric("총 용량",      f"{total_volume:,.0f} L")
    days = max((plan_end - plan_start).days, 1)
    p3.metric("일 평균 생산", f"{plan_qty // days:,} 개/일")

    st.markdown('<div class="section-title">생산 일정표</div>', unsafe_allow_html=True)
    schedule   = [
        ("원료 입고 확인",  "원료팀",  "완료"),
        ("설비 세팅 & CIP", "생산팀",  "완료"),
        ("시험 생산",       "QC팀",    "진행 중"),
        ("본 생산",         "생산팀",  "대기"),
        ("품질 검사",       "QC팀",    "대기"),
        ("출하",            "물류팀",  "대기"),
    ]
    badge_map = {"완료": "badge-green", "진행 중": "badge-yellow", "대기": "badge-blue"}
    rows_html = "".join(
        f"<tr><td>{s[0]}</td><td>{s[1]}</td>"
        f"<td><span class='badge {badge_map[s[2]]}'>{s[2]}</span></td></tr>"
        for s in schedule
    )
    st.markdown(f"""
    <table class="plan-table">
      <tr><th>단계</th><th>담당</th><th>상태</th></tr>
      {rows_html}
    </table>
    """, unsafe_allow_html=True)