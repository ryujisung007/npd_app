import streamlit as st

def _load_api_keys():
    try:
        return st.secrets["NAVER_CLIENT_ID"], st.secrets["NAVER_CLIENT_SECRET"]
    except:
        pass
    import os
    cid  = os.environ.get("NAVER_CLIENT_ID")
    csec = os.environ.get("NAVER_CLIENT_SECRET")
    if cid and csec:
        return cid, csec
    env_path = ".env"
    import os.path
    if os.path.exists(env_path):
        env = {}
        with open(env_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
        return env.get("NAVER_CLIENT_ID"), env.get("NAVER_CLIENT_SECRET")
    return None, None

def run():
    st.markdown("# 📊 시장조사 시스템")
    st.markdown("##### 식품 시장 현황 데이터를 수집·분석하여 전략적 의사결정을 지원합니다.")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛒 수집 상품 수", "2,847")
    c2.metric("🏪 참여 쇼핑몰", "342")
    c3.metric("📂 식품 카테고리", "15")
    c4.metric("📅 최종 업데이트", "오늘")

    st.markdown("<br>", unsafe_allow_html=True)
    tabs = st.tabs(["🛒 식품시장현황분석", "🏭 품목제조보고분석", "💰 신제품 매출 집계"])

    with tabs[0]:
        st.markdown("### 🛒 식품시장현황분석")
        CLIENT_ID, CLIENT_SECRET = _load_api_keys()
        if not CLIENT_ID:
            st.warning("⚠️ API 키 미설정 — Streamlit Secrets에 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 등록 필요")

        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            keyword = st.text_input("🔍 검색어", placeholder="예: 라면, 음료, 과자...", key="B_kw")
        with col2:
            display = st.selectbox("수집 수", [10, 20, 50, 100], index=1, key="B_disp")
        with col3:
            sort = st.selectbox("정렬", ["sim","asc","dsc","date"],
                                format_func=lambda x: {"sim":"정확도","asc":"가격↑","dsc":"가격↓","date":"날짜"}[x], key="B_sort")

        if st.button("🚀 수집 시작", key="B_collect"):
            if not CLIENT_ID:
                st.error("API 키를 먼저 설정하세요.")
            elif not keyword:
                st.warning("검색어를 입력하세요.")
            else:
                import requests, time
                from collections import defaultdict
                url = "https://openapi.naver.com/v1/search/shop.json"
                headers = {"X-Naver-Client-Id": CLIENT_ID, "X-Naver-Client-Secret": CLIENT_SECRET}
                params  = {"query": keyword, "display": display, "sort": sort}
                with st.spinner(f"'{keyword}' 수집 중..."):
                    resp = requests.get(url, headers=headers, params=params)
                if resp.status_code == 200:
                    items = resp.json().get("items", [])
                    import pandas as pd
                    rows = [{
                        "상품명":   i["title"].replace("<b>","").replace("</b>",""),
                        "카테고리": i.get("category2",""),
                        "최저가":   int(i["lprice"]) if i["lprice"] else 0,
                        "쇼핑몰":   i["mallName"],
                        "productId":i.get("productId",""),
                    } for i in items if i.get("category1") == "식품"]
                    if rows:
                        df = pd.DataFrame(rows)
                        st.success(f"✅ {len(df)}개 수집 완료")
                        st.dataframe(df, use_container_width=True)
                        st.session_state["B_df"] = df
                    else:
                        st.info("식품 카테고리 상품이 없습니다.")
                else:
                    st.error(f"API 오류: {resp.status_code}")

        if "B_df" in st.session_state:
            import io, pandas as pd
            buf = io.BytesIO()
            st.session_state["B_df"].to_excel(buf, index=False, engine="openpyxl")
            st.download_button("📥 엑셀 저장", buf.getvalue(),
                               file_name=f"{keyword}_수집결과.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with tabs[1]:
        st.markdown("### 🏭 품목제조보고분석")
        st.info("품목제조보고서 데이터 분석 기능 — 연동 예정")

    with tabs[2]:
        st.markdown("### 💰 신제품 매출 집계")
        st.info("매출 집계 기능 — 연동 예정")
