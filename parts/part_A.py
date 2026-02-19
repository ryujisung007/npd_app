# --------------------------------------------------------
# AI 통합 보고서 (전문 리포트 스타일)
# --------------------------------------------------------
if openai_enabled:

    with st.spinner("AI 전략 보고서 생성 중..."):

        client = OpenAI(
            api_key=st.secrets["openai"]["OPENAI_API_KEY"]
        )

        prompt = f"""
        쇼핑 데이터 요약:
        평균가격: {df_shop['lprice'].mean()}
        브랜드 순위: {brand_rank.to_dict()}

        위 데이터를 기반으로 시장 경쟁구조, 가격 전략,
        유망 플레이버 방향, 신규 진입 전략을 제안하세요.
        """

        response_ai = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )

    report_text = response_ai.choices[0].message.content

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

else:
    st.info("OpenAI 키가 없어 AI 보고서는 비활성화됩니다.")
