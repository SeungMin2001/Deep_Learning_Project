# -*- coding: utf-8 -*-
import pandas as pd
import os
from sentence_transformers import SentenceTransformer
from umap import UMAP
from hdbscan import HDBSCAN
from bertopic import BERTopic

class Step4_1_GTM:
    def GTM1(self):
        """
        BERTopic 결과를 CSV 파일로 변환하여 저장하기
        """
        try:
            # 필터링된 특허 데이터 읽기
            filter_file_path = 'extract_end.csv'
            if os.path.exists(filter_file_path):
                print("✅ 필터링된 데이터 사용")
                filtered_df = pd.read_csv(filter_file_path)
                if filtered_df.empty:
                    print("❌ 필터링된 데이터가 비어있습니다.")
                    return False
                # 필터링된 데이터에서는 'text' 컬럼 사용
                lemmatized_patents = filtered_df['lemmatized_text'].dropna().tolist()
                patent_prep = filtered_df['text'].dropna().tolist()
            else:
                # 대안으로 extract_end.csv 사용
                filtered_df = pd.read_csv('extract_end.csv')
                
                if filtered_df.empty:
                    print("❌ 데이터가 없습니다.")
                    return False
                    
                # 전처리된 텍스트 리스트 생성
                lemmatized_patents = filtered_df['lemmatized_text'].dropna().tolist()
                patent_prep = filtered_df['text'].dropna().tolist()
            
            if not lemmatized_patents:
                print("❌ 전처리된 텍스트가 없습니다.")
                return False
            
            print(f"✅ {len(lemmatized_patents)}개의 문서로 토픽 모델링 시작")
            
            # BERTopic 모델 설정
            embedding_model = SentenceTransformer('jhgan/ko-sroberta-multitask')
            
            # UMAP 차원 축소
            umap_model = UMAP(
                n_neighbors=15,
                n_components=5,
                min_dist=0.0,
                metric='cosine',
                random_state=42
            )
            
            # HDBSCAN 클러스터링
            hdbscan_model = HDBSCAN(
                min_cluster_size=15,
                metric='euclidean',
                cluster_selection_method='eom',
                prediction_data=True
            )
            
            # BERTopic 모델 생성
            topic_model = BERTopic(
                embedding_model=embedding_model,
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                nr_topics="auto",
                calculate_probabilities=True,
                verbose=True
            )
            
            # 토픽 모델 훈련
            topics, probabilities = topic_model.fit_transform(lemmatized_patents)

            # --------------------------------------------------------------
            # DataFrame 생성: 문서 ID(또는 텍스트)와 토픽 확률 분포를 하나의 테이블로 결합
            # --------------------------------------------------------------

            # 확률 분포 행렬(probabilities)을 DataFrame으로 변환
            n_topics = probabilities.shape[1]
            prob_df = pd.DataFrame(
                probabilities,
                columns=[f"Topic_{i}" for i in range(n_topics)]
            )

            # 문서 식별용 컬럼(Document)을 확률 분포 DataFrame 앞에 추가
            prob_df.insert(0, "Document", patent_prep)

            # 대표 토픽(최댓값을 가진 토픽 인덱스) 컬럼 추가
            prob_df["Dominant_Topic"] = topics

            # CSV 파일로 저장
            output_path = "BERTopic_topic_distribution.csv"
            prob_df.to_csv(output_path, index=False)

            print(f"BERTopic 토픽 분포가 '{output_path}' 파일로 저장되었습니다.")
            return True
            
        except Exception as e:
            print(f"❌ GTM1 메서드 실행 중 오류 발생: {str(e)}")
            return False

    def GTM2(self):
        """
        GTM2 메서드 - 추가 GTM 관련 기능이 있다면 여기에 구현
        """
        import pandas as pd
        import numpy as np
        try:
            from ugtm import eGTM
            import altair as alt
            from sklearn.preprocessing import StandardScaler
            
            # GTM2 관련 코드를 여기에 추가할 수 있습니다
            print("GTM2 메서드가 호출되었습니다.")
            # 필요한 GTM2 로직을 여기에 구현하세요
            pass
        except ImportError as e:
            print(f"GTM2 실행에 필요한 라이브러리가 없습니다: {e}")
            return False

if __name__ == "__main__":
    # 테스트 실행
    gtm = Step4_GTM()
    result = gtm.GTM1()
    print(f"GTM1 실행 결과: {result}")