import streamlit as st
import requests
import json
import urllib.parse
import pandas as pd
import plotly.graph_objects as go
from datetime import date
import re

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# ── 공통 DB ──
BEVERAGE_STRUCTURE = {
    "건강기능성음료": {
        "플레이버": ["망고", "베리", "레몬", "복숭아", "초코"],
        "브랜드":   ["몬스터", "레드불", "셀시어스", "마이밀", "닥터유"],
    },
    "탄산음료": {
        "플레이버": ["콜라", "레몬", "자몽", "라임", "청포도"],
        "브랜드":   ["코카콜라", "펩시", "칠성사이다", "환타"],
    },
    "과일주스": {
        "플레이버": ["오렌지", "사과", "망고", "포도", "타트체리"],
        "브랜드":   ["델몬트", "썬키스트", "따옴", "돈시몬"],
    },
    "전통/차음료": {
        "플레이버": ["녹차", "홍차", "보리차", "식혜", "쌍화차"],
        "브랜드":   ["동서", "광동", "웅진"],
    },
    "제로/저당음료": {
        "플레이버": ["제로콜라", "제로사이다", "무가당레몬"],
        "브랜드":   ["코카콜라제로", "펩시제로", "칠성제로"],
    },
}

STANDARD_VOLUME = {
    "건강기능성음료": 355,
    "탄산음료": 355,
    "과일주스": 200,
    "전통/차음료": 240,
    "제로/저당음료": 355,
}

DATALAB_KEYWORDS = {
    "건강기능성음료": ["에너지음료", "비타민음료", "단백질음료", "기능성음료"],
    "탄산음료":       ["콜라", "사이다", "이온음료", "과즙탄산음료"],
    "과일주스":       ["오렌지주스", "사과주스", "망고주스", "레몬주스"],
    "전통/차음료":    ["식혜", "녹차음료", "홍차음료", "보리차"],
    "제로/저당음료":  ["제로음료", "저당음료", "무설탕음료"],
}


def strip_html(text):
    return re.sub(r"<[^>]+>", "", text)


def flavor_brand_selector():
    selected_group = st.selectbox("📂 분석 계열", list(BEVERAGE_STRUCTURE.keys()), key="mkt_group")
    flavors_list = ["없음"] + BEVERAGE_STRUCTURE[selected_group]["플레이버"]
    brands_list  = ["없음"] + BEVERAGE_STRUCTURE[selected_group]["브랜드"]

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        f_sel = st.selectbox("추천 플레이버", flavors_list, key="mkt_fsel")
    with col_f2:
        f_cus = st.text_input("직접입력(플레이버)", key="mkt_fcus", placeholder="없음 선택 후 입력")
    final_flavor = f_cus.strip() if f_cus.strip() else (f_sel if f_sel != "없음" else "")

    col_b1, col_b2 = st.columns([2, 1])
    with col_b1:
        b_sel = st.selectbox("추천 브랜드", brands_list, key="mkt_bsel")
    with col_b2:
        b_cus = st.text_input("직접입력(브랜드)", key="mkt_bcus", placeholder="없음 선택 후 입력")
    final_brand = b_cus.strip() if b_cus.strip() else (b_sel if b_sel != "없음" else "")

    return selected_group, final_flavor, final_brand


def run():
    st.markdown("""
    <style>
    .section-title {
        font-size: 15px; font-weight: 700; color: #00C8D4;
        border-left: 4px solid #00C8D4; padding-left: 10px; margin: 20px 0 12px;
    }
    .product-card {
        background: #1A2E4A; border: 1px solid #1E3A5A;
        border-radius: 10px; padding: 10px; text-align: center; height: 100%;
    }
    .product-card img { width:100%; height:120px; object-fit:contain; border-radius:6px; background:#0B1629; }
    .product-card .prod-title {
        font-size:11px; color:#E8F0FE; margin-top:6px;
        overflow:hidden; display:-webkit-box;
        -webkit-line-clamp:2; -webkit-box-orient:vertical;
    }
    .product-card .prod-price { font-size:13px; font-weight:700; color:#00C8D4; margin-top:4px; }
    .product-card a { display:block; margin-top:6px; font-size:10px; color:#7A9CC0; text-decoration:none; }
    .ai-box {
        background:#0B1629; border:1px solid #00C8D4; border-radius:12px;
        padding:20px 24px; margin-top:16px; line-height:1.8;
        font-size:14px; color:#E8F0FE; white-space:pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">음료 시장 트렌드 & 쇼핑 분석</div>', unsafe_allow_html=True)

    if "naver_search" not in st.secrets or "naver_shopping" not in st.secrets:
        st.error("네이버 API secrets가 설정되지 않았습니다.")
        return

    try:
        openai_enabled = (
            "openai" in st.secrets
            and bool(st.secrets["openai"].get("OPENAI_API_KEY"))
            and OpenAI is not None
        )
    except Exception:
        openai_enabled = False

    selected_group, final_flavor, final_brand = flavor_brand_selector()

    col_c, col_d, col_e = st.columns(3)
    with col_c:
        start_date = st.date_input("시작일", date(2023, 1, 1))
    with col_d:
        end_date = st.date_input("종료일", date.today())
    with col_e:
        time_unit = st.selectbox("📅 분석 단위", ["month", "week", "date"])

    if st.button("📊 분석 실행", key="mkt_run"):
        search_parts = [p for p in [final_brand, final_flavor] if p]
        if not search_parts:
            st.warning("⚠️ 플레이버 또는 브랜드 중 하나 이상 선택하거나 입력하세요.")
            return
        search_keyword = " ".join(search_parts)

        # ── DataLab 트렌드 ──
        keyword_groups = []
        if final_brand:
            keyword_groups.append({"groupName": final_brand, "keywords": [final_brand]})
        if final_flavor:
            keyword_groups.append({"groupName": final_flavor, "keywords": [final_flavor]})
        cat_kw = DATALAB_KEYWORDS.get(selected_group, [])
        if cat_kw:
            keyword_groups.append({"groupName": selected_group, "keywords": cat_kw})

        body = {
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate":   end_date.strftime("%Y-%m-%d"),
            "timeUnit":  time_unit,
            "keywordGroups": keyword_groups,
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
                colors = ["#00C8D4", "#B08FFF", "#FFB347", "#34d399", "#f472b6"]
                fig = go.Figure()
                for i, res in enumerate(result["results"]):
                    group_name = res["title"]
                    df_t = pd.DataFrame(res["data"])
                    df_t["period"] = pd.to_datetime(df_t["period"])
                    trend_summary[group_name] = df_t["ratio"].tolist()[-3:]
                    color = colors[i % len(colors)]
                    fig.add_trace(go.Scatter(
                        x=df_t["period"], y=df_t["ratio"],
                        mode="lines", name=group_name,
                        line=dict(color=color, width=2),
                    ))
                    fig.add_trace(go.Scatter(
                        x=df_t["period"], y=df_t["ratio"],
                        mode="markers+text", name=f"{group_name} 값",
                        marker=dict(color=color, size=8, symbol="circle",
                                    line=dict(color="white", width=1.5)),
                        text=[f"{v:.1f}" for v in df_t["ratio"]],
                        textposition="top center",
                        textfont=dict(size=9, color=color),
                        showlegend=False,
                    ))
                fig.update_layout(
                    paper_bgcolor="#0B1629", plot_bgcolor="#0B1629",
                    font=dict(color="#7A9CC0"),
                    title=dict(text=f"🔍 '{search_keyword}' 및 계열 트렌드",
                               font=dict(color="#E8F0FE", size=14)),
                    hovermode="x unified",
                    legend=dict(bgcolor="#1A2E4A", bordercolor="#1E3A5A",
                                font=dict(color="#E8F0FE")),
                    xaxis=dict(gridcolor="#1A2E4A", color="#7A9CC0"),
                    yaxis=dict(gridcolor="#1A2E4A", color="#7A9CC0"),
                    margin=dict(t=50, b=30),
                )
                st.plotly_chart(fig, use_container_width=True)

        # ── 쇼핑 분석 ──
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

                st.markdown(f'<div class="section-title">🛍 쇼핑 현황 — "{search_keyword}"</div>',
                            unsafe_allow_html=True)

                avg_price    = df_shop["lprice"].mean()
                min_price    = df_shop["lprice"].min()
                per_unit_est = df_shop["lprice"].median() / 6

                m1, m2, m3, m4 = st.columns(4)
                m1.metric("평균 가격",        f"{avg_price:,.0f} 원")
                m2.metric("최저 가격",        f"{min_price:,.0f} 원")
                m3.metric("개당 가격 (예측)", f"≈ {per_unit_est:,.0f} 원")
                m4.metric("상품 수",          f"{len(df_shop):,} 개")

                # 이미지 카드
                st.markdown('<div class="section-title">🖼 상품 목록 (이미지·링크)</div>', unsafe_allow_html=True)
                image_items = [it for it in items if it.get("image")][:12]
                if image_items:
                    cols_per_row = 4
                    for row_start in range(0, len(image_items), cols_per_row):
                        row_items = image_items[row_start:row_start + cols_per_row]
                        img_cols = st.columns(cols_per_row)
                        for col, it in zip(img_cols, row_items):
                            title_clean = strip_html(it.get("title", ""))
                            price_val   = it.get("lprice", "0")
                            link_url    = it.get("link", "#")
                            img_url     = it.get("image", "")
                            with col:
                                st.markdown(f"""
                                <div class="product-card">
                                    <img src="{img_url}" onerror="this.style.display='none'" />
                                    <div class="prod-title">{title_clean}</div>
                                    <div class="prod-price">{int(price_val):,} 원</div>
                                    <a href="{link_url}" target="_blank">🔗 구매 링크</a>
                                </div>
                                """, unsafe_allow_html=True)

                # 전체 테이블
                st.markdown('<div class="section-title">📋 전체 상품 테이블</div>', unsafe_allow_html=True)
                df_display = df_shop.copy()
                df_display["상품명"] = df_display["title"].apply(strip_html)
                st.dataframe(
                    df_display[["상품명", "lprice", "brand", "mallName"]].rename(columns={
                        "lprice": "최저가", "brand": "브랜드", "mallName": "쇼핑몰"
                    }),
                    use_container_width=True, height=220
                )

                # 브랜드 노출순위 + 평균가 겹치기
                st.markdown('<div class="section-title">🏆 브랜드 노출순위 + 평균가</div>', unsafe_allow_html=True)
                brand_rank = df_shop["brand"].value_counts().reset_index()
                brand_rank.columns = ["브랜드", "노출건수"]
                brand_avg = df_shop.groupby("brand")["lprice"].agg(["mean", "std"]).reset_index()
                brand_avg.columns = ["브랜드", "평균가", "표준편차"]
                brand_avg["표준편차"] = brand_avg["표준편차"].fillna(0)
                brand_merged = brand_rank.merge(brand_avg, on="브랜드", how="left")

                fig_brand = go.Figure()
                fig_brand.add_trace(go.Bar(
                    x=brand_merged["브랜드"], y=brand_merged["노출건수"],
                    name="노출건수", marker_color="#00C8D4", opacity=0.85, yaxis="y1",
                ))
                fig_brand.add_trace(go.Scatter(
                    x=brand_merged["브랜드"], y=brand_merged["평균가"],
                    mode="lines+markers+text", name="브랜드 평균가",
                    line=dict(color="#B08FFF", width=2),
                    marker=dict(size=8, color="#B08FFF", line=dict(color="white", width=1.5)),
                    text=[f"{v:,.0f}원" for v in brand_merged["평균가"]],
                    textposition="top center", textfont=dict(size=9, color="#B08FFF"),
                    error_y=dict(type="data", array=brand_merged["표준편차"].tolist(),
                                 visible=True, color="#B08FFF", thickness=1.5, width=4),
                    yaxis="y2",
                ))
                fig_brand.update_layout(
                    paper_bgcolor="#0B1629", plot_bgcolor="#0B1629",
                    font=dict(color="#7A9CC0"),
                    title=dict(text="브랜드 노출건수 + 평균가(표준편차)",
                               font=dict(color="#E8F0FE", size=13)),
                    hovermode="x unified",
                    legend=dict(bgcolor="#1A2E4A", bordercolor="#1E3A5A", font=dict(color="#E8F0FE")),
                    xaxis=dict(gridcolor="#1A2E4A", color="#7A9CC0"),
                    yaxis=dict(title="노출건수", gridcolor="#1A2E4A", color="#00C8D4"),
                    yaxis2=dict(title="평균 가격 (원)", overlaying="y", side="right",
                                color="#B08FFF", showgrid=False),
                    margin=dict(t=50, b=30),
                )
                st.plotly_chart(fig_brand, use_container_width=True)

                # 브랜드 평균가 + 개당 예측가
                st.markdown('<div class="section-title">💰 브랜드 평균 가격 (개당 예측 포함)</div>',
                            unsafe_allow_html=True)
                brand_price = df_shop.groupby("brand")["lprice"].agg(["mean", "std", "count"]).reset_index()
                brand_price.columns = ["브랜드", "평균가", "표준편차", "상품수"]
                brand_price["표준편차"]   = brand_price["표준편차"].fillna(0)
                brand_price["개당예측가"] = brand_price["평균가"] / 6
                brand_price = brand_price.sort_values("평균가", ascending=False)

                fig_price = go.Figure()
                fig_price.add_trace(go.Bar(
                    x=brand_price["브랜드"], y=brand_price["평균가"],
                    name="묶음 평균가", marker_color="#00C8D4", opacity=0.8,
                    error_y=dict(type="data", array=brand_price["표준편차"].tolist(),
                                 visible=True, color="#00F0FF", thickness=2, width=6),
                    text=[f"{v:,.0f}원" for v in brand_price["평균가"]],
                    textposition="outside", textfont=dict(size=9, color="#00C8D4"),
                ))
                fig_price.add_trace(go.Scatter(
                    x=brand_price["브랜드"], y=brand_price["개당예측가"],
                    mode="lines+markers+text", name="개당 예측가 (÷6)",
                    line=dict(color="#FFB347", width=2, dash="dot"),
                    marker=dict(size=8, color="#FFB347", line=dict(color="white", width=1.5)),
                    text=[f"≈{v:,.0f}원" for v in brand_price["개당예측가"]],
                    textposition="bottom center", textfont=dict(size=9, color="#FFB347"),
                ))
                fig_price.update_layout(
                    paper_bgcolor="#0B1629", plot_bgcolor="#0B1629",
                    font=dict(color="#7A9CC0"),
                    title=dict(text="브랜드 평균가(막대) + 개당 예측가(선, ÷6 기준)",
                               font=dict(color="#E8F0FE", size=13)),
                    hovermode="x unified",
                    legend=dict(bgcolor="#1A2E4A", bordercolor="#1E3A5A", font=dict(color="#E8F0FE")),
                    xaxis=dict(gridcolor="#1A2E4A", color="#7A9CC0"),
                    yaxis=dict(gridcolor="#1A2E4A", color="#7A9CC0"),
                    margin=dict(t=60, b=30),
                )
                st.plotly_chart(fig_price, use_container_width=True)

                bp = brand_price.copy()
                bp["평균가"]    = bp["평균가"].apply(lambda x: f"{x:,.0f} 원")
                bp["개당예측가"] = bp["개당예측가"].apply(lambda x: f"≈ {x:,.0f} 원")
                bp["표준편차"]  = bp["표준편차"].apply(lambda x: f"±{x:,.0f}")
                st.dataframe(bp[["브랜드", "평균가", "개당예측가", "표준편차", "상품수"]],
                             use_container_width=True)

                shopping_summary = {
                    "평균가격": float(df_shop["lprice"].mean()),
                    "브랜드순위": brand_rank.to_dict(),
                }
            else:
                st.info("쇼핑 검색 결과가 없습니다.")

        # ── AI 보고서 ──
        if openai_enabled:
            st.markdown('<div class="section-title">🤖 AI 통합 전략 보고서</div>', unsafe_allow_html=True)
            with st.spinner("AI 분석 중..."):
                client = OpenAI(api_key=st.secrets["openai"]["OPENAI_API_KEY"])
                prompt = f"""
                검색 키워드: {search_keyword}
                트렌드 데이터: {trend_summary}
                쇼핑 데이터: {shopping_summary}
                시장 성장성, 브랜드 경쟁 구조, 가격 전략, 신규 진입 전략을 종합 보고서로 작성하세요.
                """
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                )
            st.markdown(f'<div class="ai-box">{resp.choices[0].message.content}</div>',
                        unsafe_allow_html=True)
        else:
            st.info("OpenAI 키가 없어 AI 보고서는 비활성화됩니다.")