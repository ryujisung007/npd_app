import streamlit as st
import pandas as pd
from datetime import date

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

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
    .ai-box {
        background:#0B1629; border:1px solid #00C8D4; border-radius:12px;
        padding:20px 24px; margin-top:16px; line-height:1.8;
        font-size:14px; color:#E8F0FE; white-space:pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

    try:
        openai_enabled = (
            "openai" in st.secrets
            and bool(st.secrets["openai"].get("OPENAI_API_KEY"))
            and OpenAI is not None
        )
    except Exception:
        openai_enabled = False

    st.markdown('<div class="section-title">개발보고서 작성</div>', unsafe_allow_html=True)

    selected_group = st.selectbox("📂 제품 계열", list(BEVERAGE_STRUCTURE.keys()), key="rep_group")
    flavors_list   = ["없음"] + BEVERAGE_STRUCTURE[selected_group]["플레이버"]
    brands_list    = ["없음"] + BEVERAGE_STRUCTURE[selected_group]["브랜드"]

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        f_sel = st.selectbox("🍊 플레이버", flavors_list, key="rep_fsel")
        f_cus = st.text_input("직접입력(플레이버)", key="rep_fcus", placeholder="없음 선택 후 입력")
        final_flavor = f_cus.strip() if f_cus.strip() else (f_sel if f_sel != "없음" else "")
        rep_manager  = st.text_input("담당자", placeholder="홍길동", key="rep_manager")
        rep_date     = st.date_input("보고서 작성일", date.today(), key="rep_date")
    with col_r2:
        b_sel = st.selectbox("🏷 브랜드", brands_list, key="rep_bsel")
        b_cus = st.text_input("직접입력(브랜드)", key="rep_bcus", placeholder="없음 선택 후 입력")
        final_brand = b_cus.strip() if b_cus.strip() else (b_sel if b_sel != "없음" else "")
        rep_version = st.selectbox("버전", ["v1.0", "v1.1", "v2.0", "최종"], key="rep_ver")
        rep_status  = st.selectbox("진행 상태", ["개발 중", "시험 생산", "승인 대기", "완료"], key="rep_status")

    rep_product = f"{final_brand} {final_flavor}".strip() or "미입력"

    st.markdown('<div class="section-title">개발 내용</div>', unsafe_allow_html=True)

    rep_concept = st.text_area("📌 제품 컨셉 & 개발 배경", height=80, placeholder="소비자 트렌드, 개발 목적 등", key="rep_concept")
    rep_formula = st.text_area("🧬 배합비 요약", height=80, placeholder="주요 원료 및 함량 요약", key="rep_formula")
    rep_sensory = st.text_area("👅 관능 평가 결과", height=80, placeholder="색상, 향, 맛, 전체적 기호도 등", key="rep_sensory")
    rep_quality = st.text_area("🔬 품질 규격", height=80, placeholder="당도, pH, 미생물, 이화학 규격 등", key="rep_quality")
    rep_issue   = st.text_area("⚠️ 이슈 & 개선사항", height=80, placeholder="발생 이슈 및 해결 방안", key="rep_issue")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("🤖 AI 보고서 초안 생성", key="rep_ai_btn"):
            if openai_enabled:
                client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])
                with st.spinner("AI 보고서 작성 중..."):
                    prompt = f"""
                    제품명: {rep_product}, 계열: {selected_group}
                    플레이버: {final_flavor}, 브랜드: {final_brand}
                    담당자: {rep_manager}, 버전: {rep_version}
                    컨셉: {rep_concept}
                    배합비: {rep_formula}
                    관능평가: {rep_sensory}
                    품질규격: {rep_quality}
                    이슈: {rep_issue}
                    위 내용으로 신제품 개발 보고서를 전문적으로 작성하세요.
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
        if st.button("💾 보고서 저장", key="rep_save_btn"):
            st.success(f"✅ [{rep_product}] {rep_version} 보고서가 저장되었습니다.")

    if "report_ai_text" in st.session_state:
        st.markdown('<div class="section-title">📄 AI 생성 보고서</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="ai-box">{st.session_state["report_ai_text"]}</div>',
                    unsafe_allow_html=True)

    st.markdown('<div class="section-title">📁 최근 보고서 목록</div>', unsafe_allow_html=True)
    history = pd.DataFrame({
        "제품명":  ["몬스터 망고", "코카콜라 제로", "홍차 라떼", "델몬트 타트체리", "닥터유 베리"],
        "버전":    ["v2.0", "최종", "v1.1", "최종", "v1.0"],
        "담당자":  ["김개발", "이연구", "박기획", "최분석", "정연구"],
        "작성일":  ["2025-01-15", "2025-01-10", "2024-12-20", "2024-12-05", "2024-11-28"],
        "상태":    ["승인 대기", "완료", "완료", "완료", "개발 중"],
    })
    st.dataframe(history, use_container_width=True)