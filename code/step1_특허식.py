import os
import openai
from openai import OpenAI
from dotenv import load_dotenv

class Step1:
    def __init__(self):
        # 환경변수에서 API 키 읽기, 없으면 기본값 사용
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. OPENAI_API_KEY 환경변수를 설정해주세요.")
        self.openai = OpenAI(api_key=api_key)

    def make(self, keyword):
        MODEL = 'gpt-3.5-turbo'
        # 1) 사용자 키워드 입력 (인자로 받음)
        # 2) LLM을 통해 검색식 생성
        system_prompt = (
            "너는 특허 검색 전문가야.\n"
            "사용자가 입력한 키워드를 기반으로 관련된 10개 내외의 복합 키워드를 만들어.\n"
            "반드시 한글 키워드(동의어, 응용 포함)와 영어 키워드(약어 또는 full term)를 모두 포함해야 하고,\n"
            "검색식에는 자율주행, 물류, AGV, SLAM, 플랫폼 등 응용 분야 키워드도 확장해서 넣어.\n"
            "예: 키워드 '자율주행로봇' → 자율주행로봇, 자율이동로봇, AMR, Autonomous Mobile Robot, "
            "무인운반로봇, AGV, Automated Guided Vehicle, Warehouse Robot, SLAM 로봇, 스마트로봇\n\n"
            "출력은 반드시 다음 형식으로:\n"
            "['키워드1','키워드2','키워드3']\n"
            "다른 설명이나 문장은 출력하지 마."
        )
        user_prompt = f"키워드: {keyword}"

        response = self.openai.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0
        )
        # 응답에서 검색식만 추출
        query = response.choices[0].message.content.strip()

        # 3) 결과 출력
        #print("\n✅ KIPRIS용 특허 검색식:")
        #print(query)
        return query