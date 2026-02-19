import pandas as pd
from openai import OpenAI
import streamlit as st
import json

def generate_food_formula(info):
    """최초 정밀 배합비 생성 함수"""
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    prompt = f"""
    당신은 식품기술사이자 식품공학 박사입니다. 다음 조건으로 제조 현장용 정밀 배합비를 설계하세요.
    
    1. 식품유형: {info['category']} > {info['sub_category']}
    2. 플레이버: {info['flavor_name']}
    3. 주요 컨셉: {info['concept']}
    
    [요구사항]
    - JSON 리스트 형식 응답.
    - 배합비 합계는 100.00%.
    - '설계근거' 필드(3줄 이내) 포함.
    - 컬럼: "원료명", "배합비(%)", "사용 목적", "용도", "용법", "사용주의사항"
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Professional Food Scientist. Output ONLY JSON."},
                      {"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        result = json.loads(response.choices[0].message.content)
        # 다양한 JSON 키 구조에 대응
        data = result.get('ingredients', list(result.values())[0])
        if not isinstance(data, list): # 만약 리스트가 아니라면 내부 리스트 탐색
            data = list(result.values())[0]
            
        df = pd.DataFrame(data)
        reasoning = result.get('설계근거', "식품공전 규격에 최적화된 설계입니다.")
        return df, reasoning
    except Exception as e:
        return pd.DataFrame(), str(e)

def update_formula_with_chat(current_df, user_request):
    """채팅 피드백을 반영하여 배합비를 수정하는 함수"""
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    current_data_str = current_df.to_json(orient='records', force_ascii=False)

    prompt = f"""
    당신은 대한민국 최고 권위의 식품 R&D 전문가입니다.
    
    [현재 배합비 데이터]
    {current_data_str}
    
    [사용자의 수정 요청]
    "{user_request}"
    
    위 요청을 기술적으로 검토하여 배합비를 수정하십시오. 
    1. 배합비 합계는 반드시 100.00%를 유지해야 합니다.
    2. 수정된 원료의 '사용주의사항'이나 '용법'도 전문가 수준으로 업데이트하십시오.
    3. 응답은 {{"updated_ingredients": [...], "reason": "수정 근거 설명"}} 형식의 JSON으로만 하십시오.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Update the food formula precisely based on feedback. Respond in JSON."},
                      {"role": "user", "content": prompt}],
            response_format={ "type": "json_object" }
        )
        result = json.loads(response.choices[0].message.content)
        
        # 수정된 리스트 추출
        raw_list = result.get('updated_ingredients', [])
        if not raw_list:
             raw_list = list(result.values())[0]
             
        new_df = pd.DataFrame(raw_list)
        return new_df, result.get('reason', "요청하신 기술적 피드백을 레시피에 반영했습니다.")
    except Exception as e:
        return current_df, f"수정 작업 중 기술적 오류가 발생했습니다: {e}"