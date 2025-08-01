import pandas as pd
import ast
import os

class Step3_5:
    def __init__(self):
        pass
    
    def generate_graph(self, keywords=None):
        """
        특허 연도별 그래프 생성
        
        Args:
            keywords: 분석할 키워드 리스트 (Step1에서 생성된 키워드)
                     None이면 기본 키워드 사용
        
        Returns:
            final_df: 연도별 특허 출원 동향 데이터
        """
        print(f"🔍 Step3_5 시작 - 입력 키워드: {keywords}")
        
        try:
            import os  # 함수 내부에서 명시적으로 import
            
            # CSV 파일 존재 확인
            if not os.path.exists("./extract_end.csv"):
                print("❌ extract_end.csv 파일이 존재하지 않습니다.")
                return None
                
            print("📁 extract_end.csv 파일 읽는 중...")
            # CSV 읽기
            df = pd.read_csv("./extract_end.csv")
            print(f"📊 CSV 데이터 로드 완료 - 행 수: {len(df)}")
            
            # 키워드 설정
            if keywords is None:
                # 기본 키워드
                KEYWORDS = ["자율주행", "로봇", "배터리", "전기차", "AI", "인공지능"]
            else:
                # Step1에서 전달받은 키워드 사용
                if isinstance(keywords, str):
                    try:
                        KEYWORDS = ast.literal_eval(keywords)
                    except:
                        KEYWORDS = ["자율주행", "로봇", "배터리", "전기차", "AI", "인공지능"]
                else:
                    KEYWORDS = keywords
            
            print(f"사용할 키워드: {KEYWORDS}")
            
            # 📌 날짜 전처리: 포맷 통일 + 연도 추출
            df["출원일"] = df["출원일"].astype(str).str.strip()  # 공백 제거
            df["출원연도"] = pd.to_datetime(
                df["출원일"], errors="coerce", infer_datetime_format=True
            ).dt.year

            # 모든 키워드에 해당하는 특허 데이터 통합
            all_matched_patents = pd.DataFrame()
            total_count = 0

            for kw in KEYWORDS:
                # 키워드 필터링
                mask = df["검색 키워드"].astype(str).str.contains(kw, case=False, na=False)
                filtered_df = df[mask].copy()

                # 데이터 건수 확인
                count = mask.sum()
                total_count += count
                print(f"**{kw}** → {count}건")

                if not filtered_df.empty:
                    # 모든 매칭된 특허를 하나로 합침
                    all_matched_patents = pd.concat([all_matched_patents, filtered_df], ignore_index=True)

            if not all_matched_patents.empty:
                # 중복 제거 (같은 특허가 여러 키워드에 매칭될 수 있음)
                all_matched_patents = all_matched_patents.drop_duplicates()
                
                # 통합된 데이터로 연도별 건수 집계 (단일 컬럼)
                year_counts = all_matched_patents.groupby("출원연도").size().reset_index(name="전체 특허 출원 건수")

                # 1990~2025 연도 범위 생성
                year_range = pd.DataFrame({"출원연도": range(1990, 2026)})
                
                # 기존 데이터와 병합하여 빈 연도도 포함
                final_df = pd.merge(year_range, year_counts, on="출원연도", how="left")
                final_df = final_df.sort_values("출원연도").fillna(0)
                
                # 출원연도를 인덱스로 설정
                final_df = final_df.set_index("출원연도")

                print(f"✅ 특허 그래프 데이터 생성 완료 - 총 {len(all_matched_patents)}건 (중복 제거 후)")
                return final_df
            else:
                print("❌ 모든 키워드에 대해 데이터가 없습니다.")
                return None
                
        except Exception as e:
            print(f"그래프 생성 중 오류 발생: {str(e)}")
            return None