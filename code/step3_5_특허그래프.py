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
            
            # CSV 파일 존재 확인 (여러 경로 시도)
            csv_paths = ["./extract_end.csv", "../extract_end.csv", "/Users/shinseungmin/Documents/벌토픽_전체코드/extract_end.csv"]
            csv_path = None
            
            for path in csv_paths:
                if os.path.exists(path):
                    csv_path = path
                    break
            
            if csv_path is None:
                print("❌ extract_end.csv 파일을 찾을 수 없습니다.")
                print(f"현재 디렉토리: {os.getcwd()}")
                return None
                
            print(f"📁 CSV 파일 읽는 중: {csv_path}")
            # CSV 읽기
            df = pd.read_csv(csv_path)
            print(f"📊 CSV 데이터 로드 완료 - 행 수: {len(df)}")
            
            # 📌 날짜 전처리: openDate 우선 사용, 없으면 출원일 사용
            print(f"원본 데이터 수: {len(df)}")
            
            # openDate 컬럼이 있는지 확인
            if 'openDate' in df.columns:
                print(f"openDate 컬럼의 NaN 개수: {df['openDate'].isna().sum()}")
                # openDate가 있는 데이터만 필터링
                df_with_date = df.dropna(subset=['openDate']).copy()
                print(f"openDate가 있는 데이터 수: {len(df_with_date)}")
                
                if len(df_with_date) > 0:
                    # openDate 형식 변환 (20240202.0 -> 2024)
                    df_with_date["openDate"] = df_with_date["openDate"].astype(str).str.replace('.0', '').str.strip()
                    df_with_date["출원연도"] = pd.to_datetime(
                        df_with_date["openDate"], format='%Y%m%d', errors="coerce"
                    ).dt.year
                    
                    # 유효한 연도만 남기기
                    df = df_with_date.dropna(subset=['출원연도'])
                    print(f"openDate로부터 유효한 출원연도가 있는 데이터 수: {len(df)}")
                else:
                    print("❌ openDate가 있는 데이터가 없습니다.")
                    return None
            else:
                # openDate가 없으면 기존 출원연도 또는 출원일자 컬럼 사용
                print("openDate 컬럼이 없으므로 기존 출원연도/출원일자 데이터를 사용합니다.")
                if '출원연도' in df.columns:
                    # 이미 출원연도 컬럼이 있는 경우
                    df = df.dropna(subset=['출원연도'])
                    print(f"출원연도가 있는 데이터 수: {len(df)}")
                    if len(df) == 0:
                        print("❌ 출원연도가 있는 데이터가 없습니다.")
                        return None
                elif '출원일자' in df.columns:
                    # 출원일자 컬럼을 출원연도로 변환
                    df = df.dropna(subset=['출원일자'])
                    # 출원일자를 연도로 변환 (필요시 구현)
                    df['출원연도'] = pd.to_datetime(df['출원일자'], errors='coerce').dt.year
                    df = df.dropna(subset=['출원연도'])
                    print(f"출원일자로부터 변환된 출원연도가 있는 데이터 수: {len(df)}")
                    if len(df) == 0:
                        print("❌ 출원일자로부터 변환된 출원연도가 없습니다.")
                        return None
                elif '출원일' in df.columns:
                    df = df.dropna(subset=['출원일'])
                    # 출원일을 연도로 변환 (필요시 구현)
                    df['출원연도'] = pd.to_datetime(df['출원일'], errors='coerce').dt.year
                    df = df.dropna(subset=['출원연도'])
                    print(f"출원일로부터 변환된 출원연도가 있는 데이터 수: {len(df)}")
                    if len(df) == 0:
                        print("❌ 출원일로부터 변환된 출원연도가 없습니다.")
                        return None
                else:
                    print("❌ 날짜 관련 컬럼을 찾을 수 없습니다.")
                    return None
            
            # 최종 데이터 검증
            if len(df) == 0:
                print("❌ 날짜 전처리 후 데이터가 없습니다.")
                return None

            # 키워드 처리 및 필터링
            if keywords is None or (isinstance(keywords, list) and len(keywords) == 0):
                # None이거나 빈 리스트면 전체 데이터 사용 (키워드 필터링 없음)
                print("📊 키워드가 None이거나 비어있으므로 전체 특허 데이터를 사용합니다.")
                all_matched_patents = df.copy()
                total_count = len(all_matched_patents)
                print(f"✅ 전체 특허 수: {total_count}건")
            else:
                # 키워드가 있으면 필터링 수행
                if isinstance(keywords, str):
                    try:
                        KEYWORDS = ast.literal_eval(keywords)
                    except:
                        KEYWORDS = ["자율주행", "로봇", "배터리", "전기차", "AI", "인공지능"]
                else:
                    KEYWORDS = keywords
                
                print(f"🔍 키워드 필터링: {KEYWORDS}")
                
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
                
                if len(all_matched_patents) == 0:
                    print("❌ 키워드에 매칭된 데이터가 없습니다!")
                    return None
            
            print(f"최종 all_matched_patents 크기: {len(all_matched_patents)}")
            if not all_matched_patents.empty:
                print(f"데이터 연도 범위: {all_matched_patents['출원연도'].min()} ~ {all_matched_patents['출원연도'].max()}")
                
                # 데이터 처리 계속 진행
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

                # 연도 범위별 특허 개수 통계 출력
                print("\n📊 연도별 특허 출원 현황:")
                print(f"• 전체 특허 수: {len(all_matched_patents)}건")
                print(f"• 최초 출원연도: {int(all_matched_patents['출원연도'].min())}년")
                print(f"• 최신 출원연도: {int(all_matched_patents['출원연도'].max())}년")
                
                # 주요 연도대별 통계
                decades = {
                    "1990년대": (1990, 1999),
                    "2000년대": (2000, 2009), 
                    "2010년대": (2010, 2019),
                    "2020년대": (2020, 2025)
                }
                
                for decade, (start, end) in decades.items():
                    count = len(all_matched_patents[
                        (all_matched_patents['출원연도'] >= start) & 
                        (all_matched_patents['출원연도'] <= end)
                    ])
                    print(f"• {decade}: {count}건")

                print(f"\n✅ 특허 그래프 데이터 생성 완료 - 총 {len(all_matched_patents)}건")
                return final_df
            else:
                print("❌ 특허 데이터가 없습니다.")
                return None
                
        except Exception as e:
            print(f"그래프 생성 중 오류 발생: {str(e)}")
            return None