import streamlit as st

def run():
    st.markdown("# 🗄️ DB 검색시스템")
    st.markdown("##### 식품 관련 자료를 체계적으로 등록·분류·검색할 수 있는 통합 데이터베이스입니다.")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📥 등록 자료 수", "1,240")
    c2.metric("🗂️ 분류 카테고리", "48")
    c3.metric("🔍 이번 달 검색", "320")
    c4.metric("⬆️ 오늘 신규 등록", "12")

    st.markdown("<br>", unsafe_allow_html=True)
    tabs = st.tabs(["📥 자료등록", "🗂️ 자료분류", "📊 자료현황보기"])

    with tabs[0]:
        st.markdown("### 📥 자료등록")
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("자료명", placeholder="자료명을 입력하세요", key="D_name")
            st.selectbox("분류", ["시장조사","소비자분석","원재료정보","품질/규격","기타"], key="D_cat")
        with col2:
            st.text_area("내용 요약", placeholder="자료 내용을 간략히 입력하세요", height=100, key="D_desc")
        st.file_uploader("파일 첨부", type=["pdf","xlsx","docx","csv"], key="D_file")
        if st.button("💾 자료 등록", key="D_save"):
            st.success("자료가 등록되었습니다. (DB 연동 예정)")

    with tabs[1]:
        st.markdown("### 🗂️ 자료분류")
        import pandas as pd
        sample = pd.DataFrame({
            "자료명":  ["2026 식품트렌드 보고서","HMR 소비자 설문","라면 원재료 현황","HACCP 점검 매뉴얼"],
            "분류":    ["시장조사","소비자분석","원재료정보","품질/규격"],
            "등록일":  ["2026-02-18","2026-02-17","2026-02-16","2026-02-15"],
            "담당자":  ["홍길동","김영희","이철수","박민준"],
        })
        cat_filter = st.selectbox("분류 필터", ["전체","시장조사","소비자분석","원재료정보","품질/규격"], key="D_filter")
        df = sample if cat_filter == "전체" else sample[sample["분류"] == cat_filter]
        st.dataframe(df, use_container_width=True)

    with tabs[2]:
        st.markdown("### 📊 자료현황보기")
        import pandas as pd
        summary = pd.DataFrame({
            "카테고리": ["시장조사","소비자분석","원재료정보","품질/규격"],
            "자료 수":  [412, 287, 231, 310],
            "비율(%)":  [33, 23, 19, 25],
        })
        st.dataframe(summary, use_container_width=True)
        try:
            import altair as alt
            chart = alt.Chart(summary).mark_bar().encode(
                x=alt.X("카테고리", sort=None),
                y="자료 수",
                color=alt.Color("카테고리", scale=alt.Scale(range=["#00C8D4","#B08FFF","#FFB830","#FF6B6B"]))
            ).properties(height=250)
            st.altair_chart(chart, use_container_width=True)
        except:
            st.bar_chart(summary.set_index("카테고리")["자료 수"])
