import pandas as pd
import ast

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
        try:
            # CSV 읽기
            df = pd.read_csv("./extract_end.csv")
            
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

            # 최종 집계용 DataFrame
            final_df = pd.DataFrame()

            for kw in KEYWORDS:
                # 키워드 필터링
                mask = df["검색 키워드"].astype(str).str.contains(kw, case=False, na=False)
                filtered_df = df[mask].copy()

                # 데이터 건수 확인
                count = mask.sum()
                print(f"**{kw}** → {count}건")

                if filtered_df.empty:
                    continue

                # 연도별 건수 집계
                year_counts = filtered_df.groupby("출원연도").size().reset_index(name=kw)

                # 기존 DF와 병합
                if final_df.empty:
                    final_df = year_counts
                else:
                    final_df = pd.merge(final_df, year_counts, on="출원연도", how="outer")

            # 연도순 정렬 + NaN → 0
            if not final_df.empty:
                # 1990~2025 연도 범위 생성
                year_range = pd.DataFrame({"출원연도": range(1990, 2026)})
                
                # 기존 데이터와 병합하여 빈 연도도 포함
                final_df = pd.merge(year_range, final_df, on="출원연도", how="left")
                final_df = final_df.sort_values("출원연도").fillna(0)
                
                # 출원연도를 인덱스로 설정
                final_df = final_df.set_index("출원연도")

                print("✅ 특허 그래프 데이터 생성 완료")
                return final_df
            else:
                print("❌ 모든 키워드에 대해 데이터가 없습니다.")
                return None
                
        except Exception as e:
            print(f"그래프 생성 중 오류 발생: {str(e)}")
            return None