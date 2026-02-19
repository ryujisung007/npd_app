import streamlit as st


def run():
    st.markdown("""
    <style>
    .section-title {
        font-size: 15px; font-weight: 700; color: #00C8D4;
        border-left: 4px solid #00C8D4; padding-left: 10px; margin: 20px 0 12px;
    }
    .badge {
        display: inline-block; padding: 3px 10px; border-radius: 20px;
        font-size: 11px; font-weight: 700; margin: 2px;
    }
    .badge-blue   { background: #1e40af; color: #bfdbfe; }
    .badge-green  { background: #14532d; color: #bbf7d0; }
    .badge-yellow { background: #713f12; color: #fef08a; }
    .badge-red    { background: #7f1d1d; color: #fecaca; }
    .risk-row {
        background: #1A2E4A; border-left: 4px solid #ef4444;
        border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .risk-row.medium { border-left-color: #f59e0b; }
    .risk-row.low    { border-left-color: #22c55e; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">공정 단계별 리스크 점검</div>', unsafe_allow_html=True)

    process_step = st.selectbox(
        "🏭 공정 단계 선택",
        ["전체", "원료 입고", "전처리/용해", "배합", "살균", "충전", "포장", "출하"],
        key="risk_step"
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

    r1, r2, r3 = st.columns(3)
    r1.metric("🔴 긴급", f"{sum(1 for r in filtered if r['등급'] == 'high')} 건")
    r2.metric("🟡 주의", f"{sum(1 for r in filtered if r['등급'] == 'medium')} 건")
    r3.metric("🟢 일반", f"{sum(1 for r in filtered if r['등급'] == 'low')} 건")

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
        new_step = st.selectbox("공정 단계", ["원료 입고", "전처리/용해", "배합", "살균", "충전", "포장", "출하"], key="risk_new_step")
        new_item = st.text_input("리스크 항목", key="risk_new_item")
    with col_n2:
        new_grade  = st.selectbox("등급", ["high", "medium", "low"], key="risk_new_grade")
        new_action = st.text_input("조치 방안", key="risk_new_action")

    if st.button("➕ 리스크 등록", key="risk_add"):
        if new_item:
            st.success(f"✅ [{new_step}] '{new_item}' 리스크가 등록되었습니다.")
        else:
            st.warning("리스크 항목을 입력하세요.")