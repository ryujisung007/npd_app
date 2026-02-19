import streamlit as st
import pandas as pd
from engine_data import FOOD_CODE_MAP, get_recommended_flavors
from engine_ai import generate_food_formula, update_formula_with_chat
from io import BytesIO

st.set_page_config(page_title="식품 R&D 정밀 설계 시스템", layout="wide")

st.title("🧪 정밀 식품 배합비 설계 시스템")

# 세션 상태 초기화 (데이터 유지 및 챗봇 연동용)
if "current_df" not in st.session_state:
    st.session_state.current_df = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "reasoning" not in st.session_state:
    st.session_state.reasoning = ""

# --- 입력 섹션 ---
with st.container():
    st.subheader("📋 제품 기획 데이터 입력")
    col1, col2, col3 = st.columns(3)

    with col1:
        category = st.selectbox("1. 식품 대분류", list(FOOD_CODE_MAP.keys()))
        sub_category = st.selectbox("2. 식품 소분류 (식품공전)", FOOD_CODE_MAP[category])

    with col2:
        recom_flavors = get_recommended_flavors(category)
        selected_flavor = st.selectbox("3. AI 추천 플레이버 (TOP 10)", ["직접 입력"] + recom_flavors)
        if selected_flavor == "직접 입력":
            flavor_name = st.text_input("플레이버 직접 입력")
        else:
            flavor_name = selected_flavor

    with col3:
        concept = st.text_area("4. 주요 컨셉 (트렌드 반영)", placeholder="예: 저당, 식이섬유 강화, 천연향료만 사용")

# --- 배합비 생성 실행 ---
if st.button("🚀 정밀 배합비 생성 및 분석"):
    if flavor_name:
        input_data = {
            "category": category, 
            "sub_category": sub_category, 
            "flavor_name": flavor_name, 
            "concept": concept
        }
        
        with st.spinner('식품공전 및 시장 트렌드 분석 중...'):
            df, reasoning = generate_food_formula(input_data)
            
            if not df.empty:
                st.session_state.current_df = df
                st.session_state.reasoning = reasoning
                st.session_state.chat_history = []  # 새로운 배합 생성 시 채팅 이력 초기화
                st.rerun()  # 화면을 갱신하여 결과 표시
            else:
                st.error("데이터 생성 실패. 다시 시도해주세요.")
    else:
        st.warning("플레이버 명을 입력해주세요.")

# --- 결과 및 챗봇 섹션 ---
if st.session_state.current_df is not None:
    st.divider()
    
    # 전문가 설계 근거 출력
    st.info(f"💡 **전문가 설계 근거:** {st.session_state.reasoning}")
    
    # 배합비 표 출력
    st.subheader(f"📊 {flavor_name} {sub_category} 표준 배합비")
    st.table(st.session_state.current_df)
    
    # 엑셀 다운로드 기능
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state.current_df.to_excel(writer, index=False, sheet_name='Formula_Report')
    
    st.download_button(
        label="📥 현재 배합비 엑셀 다운로드",
        data=output.getvalue(),
        file_name=f"{flavor_name}_배합비_리포트.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # --- 챗봇 인터페이스 (대화형 수정) ---
    st.divider()
    st.subheader("💬 AI 연구원과 배합비 정밀 튜닝")
    st.write("요청에 따라 배합비를 실시간으로 수정하고 엑셀 파일도 자동 갱신됩니다.")
    
    # 이전 대화 내용 표시
    for chat in st.session_state.chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["content"])

    # 사용자 피드백 입력 및 반영
    if user_input := st.chat_input("예: 설탕을 2% 줄이고 그만큼 알룰로스를 추가해줘."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        
        # 채팅창에 사용자 질문 즉시 표시
        with st.chat_message("user"):
            st.markdown(user_input)
            
        with st.chat_message("assistant"):
            with st.spinner("전문가적 소견으로 배합비를 수정 중입니다..."):
                updated_df, reason = update_formula_with_chat(st.session_state.current_df, user_input)
                
                # 데이터 갱신
                st.session_state.current_df = updated_df
                st.session_state.reasoning = reason
                st.session_state.chat_history.append({"role": "assistant", "content": reason})
                
                # 수정된 결과 확인을 위해 화면 리프레시
                st.rerun()