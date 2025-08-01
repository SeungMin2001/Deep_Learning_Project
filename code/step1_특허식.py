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
            #['로봇', '빅데이터', '센서', '알고리즘', '인공지능', '인터넷', '자율', '제어', '주행', '카메라']
            "관련 키워드를 리스트 안에 키워드들을 담아서 만들어줘\n"
            "예시 (키워드: 자율주행 로봇): ['자율','주행','바퀴]\n"
            "리스트 안에 키워드를 열개만 만들어줘\n"
            #"1. 로봇,2. 빅데이터,3. 센서,4. 알고리즘,5. 인공지능,6. 인터넷,7. 자율,8. 제어,9. 주행,10. 카메라 이 10개의 키워드로 10개키워드 제공해줘"
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
        print("\n✅ KIPRIS용 특허 검색식:")
        #print(query)
        return query