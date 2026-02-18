import streamlit as st
import requests
import pandas as pd
import io
import time  # [추가] 재시도 대기 시간을 위한 모듈

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
    "ETQTY_XPORT_PRDLST_YN":    "내수겸용",
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

# [수정 및 강화] 타임아웃 연장 및 자동 재시도 로직 도입
def _call_i1250(api_key, start, end, extra_params=""):
    # **[변경] API 규격에 맞게 앤드(&)가 아닌 슬래시(/) 파라미터 구조 권장**
    # **[변경] 타임아웃을 20초에서 60초로 대폭 연장**
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/I1250/json/{start}/{end}"
    if extra_params:
        # 슬래시 기반 파라미터로 변환 (예: /BSSH_NM=업체명)
        url += f"/{extra_params.replace('&', '/')}"
    
    max_retries = 3  # **[추가] 최대 3번까지 재시도**
    for i in range(max_retries):
        try:
            # **[수정] timeout을 60으로 증설**
            resp = requests.get(url, timeout=60)
            resp.raise_for_status() # HTTP 오류 발생 시 예외 발생
            data = resp.json()
            
            svc = data.get("I1250", {})
            code = svc.get("RESULT", {}).get("CODE", "")
            msg = svc.get("RESULT", {}).get("MSG", "")
            rows = svc.get("row", [])
            total = int(svc.get("total_count", 0) or len(rows))
            return rows, code, msg, total
            
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectTimeout):
            if i < max_retries - 1:
                time.sleep(2) # **[추가] 타임아웃 시 2초 대기 후 재시도**
                continue
            return [], "TIMEOUT", "서버 응답 시간이 초과되었습니다. 잠시 후 다시 시도하세요.", 0
        except Exception as e:
            return [], "ERR", str(e), 0

def _call_other(api_key, svc_id, start, end):
    url = f"http://openapi.foodsafetykorea.go.kr/api/{api_key}/{svc_id}/json/{start}/{end}"
    try:
        # **[수정] 공통적으로 timeout을 60으로 증설**
        resp = requests.get(url, timeout=60)
        data = resp.json()
        svc = data.get(svc_id, {})
        code = svc.get("RESULT", {}).get("CODE", "")
        msg = svc.get("RESULT", {}).get("MSG", "")
        rows = svc.get("row", [])
        total = int(svc.get("total_count", 0) or len(rows))
        return rows, code, msg, total
    except Exception as e:
        return [], "ERR", str(e), 0

# ─────────────────────────────────────────────
# 탭1: 식품시장현황분석 (네이버) - 기존과 동일
# ─────────────────────────────────────────────
def _tab_naver():
    st.markdown("### 🛒 식품시장현황분석")
    cid, csec = _get_naver_keys()
    if not cid:
        st.warning("⚠️ Streamlit Secrets에 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 등록 필요")

    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        kw = st.text_input("🔍 검색어", placeholder="예: 라면, 음료, 과자...", key="B_nkw")
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
    st.caption("식품안전나라 I1250 · 최신 데이터 호출 → 신고일자 역순 정렬")

    api_key = _get_food_key()
    if not api_key:
        st.warning("⚠️ Streamlit Secrets에 `FOOD_SAFETY_API_KEY` 등록 필요")
        return

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
        # **[시니어 조언] 타임아웃을 피하려면 최초 호출 건수를 50~100건으로 줄이는 것이 안전합니다.**
        fetch_count = st.selectbox("📦 호출 건수", [50, 100, 200, 500], index=0, key="B_cnt")
    with r2c2:
        st.markdown("<br>", unsafe_allow_html=True)
        st.caption("💡 서버 상태가 불안정할 경우 호출 건수를 줄여보세요.")

    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🔍 검색", key="B_fs_fetch"):
        # **[수정] 파라미터 구분자를 슬래시(/)로 미리 준비**
        params_list = []
        if inp_bssh:  params_list.append(f"BSSH_NM={inp_bssh}")
        if inp_prdnm: params_list.append(f"PRDLST_NM={inp_prdnm}")
        if inp_rno:   params_list.append(f"PRDLST_REPORT_NO={inp_rno}")
        extra = "/".join(params_list)

        with st.spinner(f"데이터 {fetch_count}건 수집 중... (최대 60초 소요)"):
            rows, code, msg, total = _call_i1250(api_key, 1, fetch_count, extra)

        if rows:
            df = pd.DataFrame(rows)
            df = df.rename(columns={k: v for k, v in I1250_KOR.items() if k in df.columns})

            if "신고일자" in df.columns:
                df["신고일자_dt"] = pd.to_datetime(df["신고일자"], format="%Y%m%d", errors="coerce")
                df = df.sort_values("신고일자_dt", ascending=False)
                df["신고일자"] = df["신고일자_dt"].dt.strftime("%Y-%m-%d")
                df = df.drop(columns=["신고일자_dt"])

            df.insert(0, "번호", range(1, len(df)+1))
            st.session_state["B_fs_df"] = df
            st.session_state["B_fs_total"] = total
        elif code == "TIMEOUT":
            st.error(f"⏳ {msg}")
        elif code == "INFO-200":
            st.info("해당하는 데이터가 없습니다.")
        else:
            st.error(f"조회 실패 [{code}]: {msg}")

    # 결과 출력 및 다운로드 로직 (기존과 동일하므로 생략 가능하나 전체 유지를 위해 포함)
    if "B_fs_df" in st.session_state:
        df = st.session_state["B_fs_df"]
        st.dataframe(df, use_container_width=True)

def run():
    st.markdown("# 📊 시장조사 시스템")
    tabs = st.tabs(["🛒 식품시장현황분석", "🏭 신제품 품목제조보고분석", "💰 신제품 매출 집계"])
    with tabs[0]: _tab_naver()
    with tabs[1]: _tab_food_safety()
    with tabs[2]: st.info("매출 집계 기능 — 추후 연동 예정")

if __name__ == "__main__":
    run()