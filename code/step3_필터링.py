import openai
from openai import OpenAI
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv

class Step3:
    def filter(self):
        return
        import os  # 함수 내부에서 명시적으로 import
        
        # extract_end.csv 파일이 이미 존재하는지 확인
        if os.path.exists('./extract_end.csv'):
            print("extract_end.csv 파일이 이미 존재합니다. 필터링 과정을 건너뜁니다.")
            return
            
        data = 'extract.csv'
        df=pd.read_csv(data)
        print(df.shape)  # 합쳐진 데이터 크기 확인
        df['combined'] = df['발명명칭'].fillna('') + ' ' + df['astrtCont'].fillna('') + ' '# + df['청구항'].fillna('')

        # OpenAI client 사용
        
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            raise ValueError("OpenAI API 키가 설정되지 않았습니다. OPENAI_API_KEY 환경변수를 설정해주세요.")
        client = OpenAI(api_key=api_key)

        # 기준 문장
        reference_text = """
        자율주행 로봇, AMR, AGV, 자율이동 로봇, SLAM, 경로 인식, 충돌회피, Autonomous Mobile Robot, 스마트 물류 로봇
        """

        # 임베딩 함수
        def get_embedding(text):
            response = client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding

        # 기준 벡터
        reference_vector = get_embedding(reference_text)

        # 임베딩 및 유사도 계산
        embeddings = []
        similarities = []

        for text in tqdm(df['combined']):
            try:
                emb = get_embedding(text)
                sim = cosine_similarity([reference_vector], [emb])[0][0]
            except:
                emb = None
                sim = 0
            embeddings.append(emb)
            similarities.append(sim)
        # 유사도 컬럼 추가
        df['유사도'] = similarities

        # 필터링 (유사도 0.7 이상만)
        df = df[df['유사도'] >= 0.0]

        # 저장
        df.to_csv('./extract_end.csv', index=False)

        # # 결과 출력
        # print("필터링 전 데이터 개수:", len(df))
        # print("필터링 후 데이터 개수:", len(df))
        # print("걸러진 데이터 개수:", len(df) - len(df))
        # print(f"관련 특허 비율: {len(filtered_df)/len(df)*100:.2f}%")
        #print("필터링 완료! 관련 특허만 saved.")

        # 업로드한 파일 경로
        #file_path = '/Users/shinseungmin/Documents/벌토픽_전체코드/code/extract_end.csv'  # 업로드한 경로에 맞게 수정

        #df = pd.read_csv(file_path)

        # 출원일자에서 년도 추출
        df['출원년도'] = df['출원일'].astype(str).str[:4].astype(int)

        # 최근 10년 필터링
        current_year = datetime.now().year
        df = df[df['출원년도'] >= (current_year - 20)]

        # 저장
        output_path = 'extract_end.csv'
        df.to_csv(output_path, index=False)

        # 결과 출력
        #rint(f"최근 10년 데이터 개수: {len(recent_10_years)}")
        #print("파일이 /content/최근10년_특허 수정.csv 에 저장되었습니다.")