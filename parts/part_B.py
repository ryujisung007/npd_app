import streamlit as st
import requests
import pandas as pd
import io

# ──────────────────────────────────────────
# Part B - 시장조사 시스템 (독립 모듈)
# ──────────────────────────────────────────

FOOD_SERVICES = [
    {"순위": 1, "서비스명": "식품(첨가물)품목제조보고", "ID": "I1250"},
    {"순위": 2, "서비스명": "개별기준규격",             "ID": "I2580"},
    {"순위": 3, "서비스명": "건강기능식품 영양DB",      "ID": "I0760"},
    {"순위": 5, "서비스명": "공통기준규격",             "ID": "I2600"},
    {"순위": 6, "서비스명": "공통기준종류",             "ID": "I2590"},
]

# I1250 실제 필드 → 한글 (공식문서 기준)
I1250_KOR = {
    "LCNS_NO":                  "인허가번호",
    "BSSH_NM":                  "업체명",
    "PRDLST_REPORT_NO":         "품목보고번호",
    "PRMS_DT":                  "신고일자",
    "PRDLST_NM":                "제품명",
    "PRDLST_DCNM":              "품목유형",
    "PRODUCTION":               "생산종료여부",
    "HIENG_LNTRT_DVS_NM":       "고열량저영양",
    "CHILD_CRTFC_YN":           "어린이인증",
    "POG_DAYCNT":               "소비기한",
    "LAST_UPDT_DTM":            "최종수정일",
    "INDUTY_CD_NM":             "업종",
    "QLITY_MNTNC_TMLMT_DAYCNT": "품질유지기한",
    "USAGE":                    "용법",
    "PRPOS":                    "용도",
    "DISPOS":                   "제품형태",
    "FRMLC_MTRQLT":             "포장재질",
    "ETQTY_XPORT_PRDLST_YN":   "내수겸용",
}

def _get_food_key():
    try:    return st.secrets["FOOD_SAFETY_API_KEY"]
    except: pass
    import os
    k = os.environ.get("FOOD_SAFETY_API_KEY")
    if k: return k
    if os.path.exists(".env"):
        for line in open(".env", encoding="utf-8"):
            if "FOOD_SAFETY_API_KEY=" in line:
                return line.strip().split("=", 1)[1]
    return None

def _get_naver_keys():
    try:    return st.secrets["NAVER_CLIENT_ID"], st.secrets["NAVER_CLIENT_SECRET"]
    except: pass
    import os
    return os.environ.get("NAVER_CLIENT_ID"), os.environ.get("NAVER_CLIENT_SECRET")

def _call_i1250(api_key, start, end, extra_params=""):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/I1250/json/{start}/{end}"
    if extra_params:
        url += f"/{extra_params}"
    try:
        resp  = requests.get(url, timeout=20)
        data  = resp.json()
        svc   = data.get("I1250", {})
        code  = svc.get("RESULT", {}).get("CODE", "")
        msg   = svc.get("RESULT", {}).get("MSG", "")
        rows  = svc.get("row", [])
        total = int(svc.get("total_count", 0) or len(rows))
        return rows, code, msg, total
    except Exception as e:
        return [], "ERR", str(e), 0

def _call_other(api_key, svc_id, start, end):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{svc_id}/json/{start}/{end}"
    try:
        resp  = requests.get(url, timeout=20)
        data  = resp.json()
        svc   = data.get(svc_id, {})
        code  = svc.get("RESULT", {}).get("CODE", "")
        msg   = svc.get("RESULT", {}).get("MSG", "")
        rows  = svc.get("row", [])
        total = int(svc.get("total_count", 0) or len(rows))
        return rows, code, msg, total
    except Exception as e:
        return [], "ERR", str(e), 0

# ─────────────────────────────────────────────
# 탭1: 식품시장현황분석 (네이버)
# ─────────────────────────────────────────────
def _tab_naver():
    st.markdown("### 🛒 식품시장현황분석")
    cid, csec = _get_naver_keys()
    if not cid:
        st.warning("⚠️ Streamlit Secrets에 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 등록 필요")

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        kw   = st.text_input("🔍 검색어", placeholder="예: 라면, 음료, 과자...", key="B_nkw")
    with c2:
        disp = st.selectbox("수집 수", [10, 20, 50, 100], index=1, key="B_ndp")
    with c3:
        sort = st.selectbox("정렬", ["sim","asc","dsc","date"],
            format_func=lambda x: {"sim":"정확도","asc":"가격↑","dsc":"가격↓","date":"날짜"}[x],
            key="B_nsort")

    if st.button("🚀 수집 시작", key="B_ngo"):
        if not cid: st.error("API 키 미설정"); return
        if not kw:  st.warning("검색어 입력 필요"); return
        headers = {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}
        with st.spinner(f"'{kw}' 수집 중..."):
            r = requests.get("https://openapi.naver.com/v1/search/shop.json",
                             headers=headers,
                             params={"query": kw, "display": disp, "sort": sort})
        if r.status_code == 200:
            items = [{"상품명": i["title"].replace("<b>","").replace("</b>",""),
                      "카테고리": i.get("category2",""),
                      "최저가": int(i["lprice"] or 0),
                      "쇼핑몰": i["mallName"],
                      "productId": i.get("productId","")}
                     for i in r.json().get("items",[]) if i.get("category1")=="식품"]
            if items:
                df = pd.DataFrame(items)
                st.success(f"✅ {len(df)}개 수집 완료")
                st.dataframe(df, use_container_width=True)
                st.session_state["B_ndf"] = df
            else:
                st.info("식품 카테고리 상품 없음")
        else:
            st.error(f"API 오류: {r.status_code}")

    if "B_ndf" in st.session_state:
        buf = io.BytesIO()
        st.session_state["B_ndf"].to_excel(buf, index=False, engine="openpyxl")
        st.download_button("📥 엑셀 저장", buf.getvalue(),
            file_name="시장현황분석.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="B_ndl")


# ─────────────────────────────────────────────
# 탭2: 신제품 품목제조보고분석 (식품안전나라 I1250)
# ─────────────────────────────────────────────
def _tab_food_safety():
    st.markdown("### 🏭 신제품 품목제조보고분석")
    st.caption("식품안전나라 I1250 · 200건 호출 → 신고일자 역순 정렬 → 품목유형 필터")

    api_key = _get_food_key()
    if not api_key:
        st.warning("⚠️ Streamlit Secrets에 `FOOD_SAFETY_API_KEY` 등록 필요")
        st.code('FOOD_SAFETY_API_KEY = "발급받은키입력"', language="toml")
        return

    # ── 검색 UI (식품안전나라 화면 참고) ──────────
    st.markdown("""
    <div style="background:#0F1E33;border:1px solid #1E3A5A;border-radius:10px;padding:16px 18px;margin-bottom:16px">
      <div style="font-size:1rem;font-weight:800;color:#fff;margin-bottom:12px">🔍 기본검색</div>
    """, unsafe_allow_html=True)

    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        inp_bssh = st.text_input("업체명", placeholder="업체명 입력", key="B_bssh")
    with r1c2:
        inp_prdnm = st.text_input("제품명", placeholder="제품명 입력", key="B_prdnm")
    with r1c3:
        inp_rno = st.text_input("품목보고번호", placeholder="품목보고번호 입력", key="B_rno")

    r2c1, r2c2 = st.columns([1, 2])
    with r2c1:
        fetch_count = st.selectbox("📦 호출 건수", [50, 100, 200, 500], index=2, key="B_cnt")
    with r2c2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("💡 API에서 최신 등록순으로 수집 후 신고일자 역순 정렬합니다.")

    st.markdown("</div>", unsafe_allow_html=True)

    # 검색 버튼
    if st.button("🔍 검색", key="B_fs_fetch", use_container_width=False):
        # 추가 파라미터 조합
        params_list = []
        if inp_bssh:  params_list.append(f"BSSH_NM={inp_bssh}")
        if inp_prdnm: params_list.append(f"PRDLST_NM={inp_prdnm}")
        if inp_rno:   params_list.append(f"PRDLST_REPORT_NO={inp_rno}")
        extra = "&".join(params_list)

        with st.spinner(f"데이터 {fetch_count}건 수집 중..."):
            rows, code, msg, total = _call_i1250(api_key, 1, fetch_count, extra)

        if rows:
            # DataFrame 변환 + 한글 컬럼
            df = pd.DataFrame(rows)
            df = df.rename(columns={k: v for k, v in I1250_KOR.items() if k in df.columns})

            # 신고일자 파싱 → 역순 정렬
            if "신고일자" in df.columns:
                df["신고일자_dt"] = pd.to_datetime(df["신고일자"], format="%Y%m%d", errors="coerce")
                df = df.sort_values("신고일자_dt", ascending=False)
                df["신고일자"] = df["신고일자_dt"].dt.strftime("%Y-%m-%d")
                df = df.drop(columns=["신고일자_dt"])

            # 번호 부여
            df.insert(0, "번호", range(1, len(df)+1))

            st.session_state["B_fs_df"]    = df
            st.session_state["B_fs_total"] = total
        elif code == "INFO-200":
            st.info("해당하는 데이터가 없습니다.")
            st.session_state.pop("B_fs_df", None)
        else:
            st.error(f"조회 실패 [{code}]: {msg}")
            st.session_state.pop("B_fs_df", None)

    # ── 결과 출력 ──────────────────────────────
    if "B_fs_df" not in st.session_state:
        return

    df    = st.session_state["B_fs_df"]
    total = st.session_state.get("B_fs_total", len(df))

    # 요약 지표
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 수집 건수",    f"{len(df):,}건")
    m2.metric("📊 전체 데이터",  f"{total:,}건")
    m3.metric("📋 품목유형 수",
              f"{df['품목유형'].nunique()}종" if "품목유형" in df.columns else "-")
    m4.metric("🏢 업체 수",
              f"{df['업체명'].nunique():,}곳"  if "업체명"  in df.columns else "-")

    st.markdown("---")

    # ── 품목유형 필터 ──────────────────────────
    if "품목유형" in df.columns:
        types = ["전체"] + sorted(df["품목유형"].dropna().unique().tolist())
        col_f1, col_f2 = st.columns([2, 3])
        with col_f1:
            sel_type = st.selectbox("📂 품목유형 필터", types, key="B_type_filter")
        with col_f2:
            search_in = st.text_input("🔎 결과 내 제품명/업체명 재검색",
                                      placeholder="입력 시 필터 적용", key="B_refilter")

        filtered = df.copy()
        if sel_type != "전체":
            filtered = filtered[filtered["품목유형"] == sel_type]
        if search_in:
            mask = (
                filtered.get("제품명", pd.Series(dtype=str)).str.contains(search_in, na=False) |
                filtered.get("업체명", pd.Series(dtype=str)).str.contains(search_in, na=False)
            )
            filtered = filtered[mask]
    else:
        filtered = df.copy()

    st.markdown(f"**📋 표시 중: {len(filtered):,}건**"
                + (f" (전체 수집 {len(df):,}건)" if len(filtered) != len(df) else ""))

    # ── 테이블 출력 (주요 컬럼 우선) ──────────
    display_cols = ["번호","신고일자","업체명","제품명","품목유형",
                    "소비기한","생산종료여부","품목보고번호","업종","내수겸용"]
    display_cols = [c for c in display_cols if c in filtered.columns]

    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        height=420,
        column_config={
            "번호":       st.column_config.NumberColumn("번호", width=60),
            "신고일자":   st.column_config.TextColumn("신고일자", width=100),
            "업체명":     st.column_config.TextColumn("업체명", width=160),
            "제품명":     st.column_config.TextColumn("제품명", width=200),
            "품목유형":   st.column_config.TextColumn("품목유형", width=120),
            "소비기한":   st.column_config.TextColumn("소비기한", width=150),
            "생산종료여부": st.column_config.TextColumn("생산종료", width=80),
            "품목보고번호": st.column_config.TextColumn("품목보고번호", width=140),
        }
    )

    # ── 상세 보기 (expander 카드) ─────────────
    with st.expander("📌 신고일자별 상세 카드 보기"):
        if "신고일자" in filtered.columns:
            dates = filtered["신고일자"].dropna().unique()
            for d in dates:
                grp = filtered[filtered["신고일자"] == d]
                st.markdown(f"**📅 {d} — {len(grp)}건**")
                for _, row in grp.iterrows():
                    nm    = row.get("제품명","-")
                    bssh  = row.get("업체명","- ")
                    ptype = row.get("품목유형","- ")
                    pog   = row.get("소비기한","- ")
                    rno   = row.get("품목보고번호","- ")
                    prod  = row.get("생산종료여부","- ")
                    color = "#FF6B6B" if prod == "예" else "#4DFFB4"
                    label = "생산종료" if prod == "예" else "생산중"

                    st.markdown(f"""
                    <div style="background:#0F1E33;border:1px solid #1E3A5A;border-radius:8px;
                                padding:12px 16px;margin:5px 0;border-left:3px solid #00C8D4">
                      <div style="display:flex;justify-content:space-between;align-items:center">
                        <span style="color:#fff;font-size:0.95rem;font-weight:800">{nm}</span>
                        <span style="background:{color}22;color:{color};font-size:0.65rem;
                               font-weight:700;padding:1px 8px;border-radius:8px">{label}</span>
                      </div>
                      <div style="margin-top:7px;display:flex;flex-wrap:wrap;gap:14px;font-size:0.78rem">
                        <span style="color:#7A9CC0">🏭 <b style="color:#E8F0FE">{bssh}</b></span>
                        <span style="color:#7A9CC0">📋 <b style="color:#00C8D4">{ptype}</b></span>
                        <span style="color:#7A9CC0">⏱️ <b style="color:#FFB830">{pog}</b></span>
                        <span style="color:#3A5A7A;font-size:0.68rem;font-family:monospace">{rno}</span>
                      </div>
                    </div>""", unsafe_allow_html=True)
                st.markdown("")

    # ── 다운로드 ──────────────────────────────
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        buf1 = io.BytesIO()
        filtered[display_cols].to_excel(buf1, index=False, engine="openpyxl")
        st.download_button("📥 필터 결과 엑셀", buf1.getvalue(),
            file_name="품목제조보고_필터.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="B_dl_filter")
    with col_dl2:
        buf2 = io.BytesIO()
        df.to_excel(buf2, index=False, engine="openpyxl")
        st.download_button("📥 전체 수집 엑셀", buf2.getvalue(),
            file_name="품목제조보고_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="B_dl_all")

    # F30: 수집 결과 보고
    with st.expander("📊 수집 결과 보고"):
        st.markdown(f"- **서비스**: 식품(첨가물)품목제조보고 (I1250)")
        st.markdown(f"- **수집 건수**: {len(df):,}건 / 전체 {total:,}건")
        st.markdown(f"- **품목유형 종류**: {', '.join(df['품목유형'].dropna().unique()[:10].tolist()) if '품목유형' in df.columns else '-'}")
        st.markdown(f"- **신고일 범위**: {df['신고일자'].iloc[-1]} ~ {df['신고일자'].iloc[0]}" if "신고일자" in df.columns else "")


# ─────────────────────────────────────────────
# 메인
# ─────────────────────────────────────────────
def run():
    st.markdown("# 📊 시장조사 시스템")
    st.markdown("##### 식품 시장 현황 데이터를 수집·분석하여 전략적 의사결정을 지원합니다.")
    st.markdown("---")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🛒 수집 상품 수", "2,847")
    c2.metric("🏪 참여 쇼핑몰",   "342")
    c3.metric("📂 식품 카테고리", "15")
    c4.metric("📅 최종 업데이트", "오늘")
    st.markdown("<br>", unsafe_allow_html=True)

    tabs = st.tabs(["🛒 식품시장현황분석", "🏭 신제품 품목제조보고분석", "💰 신제품 매출 집계"])

    with tabs[0]:
        try: _tab_naver()
        except Exception as e: st.error(f"오류: {e}")

    with tabs[1]:                      # F31: 이 탭에서만 식품안전나라 작동
        try: _tab_food_safety()
        except Exception as e: st.error(f"오류: {e}")

    with tabs[2]:
        st.markdown("### 💰 신제품 매출 집계")
        st.info("매출 집계 기능 — 추후 연동 예정")
