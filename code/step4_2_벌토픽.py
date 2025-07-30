# -*- coding: utf-8 -*-
import pandas as pd
import numpy as np
from ugtm import eGTM
import altair as alt
from sklearn.preprocessing import StandardScaler
import os

class Step4_2_GTM:
    def __init__(self, csv_path=None):
        """
        GTM 모델을 활용한 토픽 시각화 클래스
        
        Args:
            csv_path (str): BERTopic 결과 CSV 파일 경로
        """
        if csv_path is None:
            self.csv_path = "BERTopic_topic_distribution.csv"
        else:
            self.csv_path = csv_path
            
        self.data_full = None
        self.data_filtered = None
        self.prob_matrix = None
        self.gtm_modes = None
        self.gtm_means = None
        
    def load_and_preprocess_data(self):
        """
        CSV 파일 읽기 및 전처리
        """
        if not os.path.exists(self.csv_path):
            print(f"❌ CSV 파일을 찾을 수 없습니다: {self.csv_path}")
            return False
            
        # CSV 파일 읽기
        self.data_full = pd.read_csv(self.csv_path)
        
        # "Dominant_Topic" 컬럼에서 -1(잡음)인 행을 제거하여 시각화에서 제외
        self.data_filtered = self.data_full[self.data_full["Dominant_Topic"] != -1].copy().reset_index(drop=True)
        
        # GTM 입력용 수치 데이터만 분리 ("Topic_0"~"Topic_{n}" 열)
        prob_cols = [col for col in self.data_filtered.columns if col.startswith("Topic_")]
        self.prob_matrix = self.data_filtered[prob_cols].values  # shape = (n_documents_filtered, n_topics)
        
        print(f"✅ 데이터 로드 완료: {len(self.data_filtered)}개 문서, {len(prob_cols)}개 토픽")
        return True
        
    def create_gtm_modes(self, k=6, m=5, s=0.2, regul=0.1, niter=200):
        """
        GTM (Modes) 모델 생성 및 학습
        
        Args:
            k (int): GTM 격자 크기
            m (int): RBF 함수 개수
            s (float): RBF 폭
            regul (float): 정규화 계수
            niter (int): EM 알고리즘 반복 횟수
        """
        if self.prob_matrix is None:
            print("❌ 먼저 load_and_preprocess_data()를 실행하세요.")
            return False
            
        self.gtm_modes = eGTM(
            k=k,            # GTM 격자 크기
            model="modes",  # "modes" 옵션 선택
            m=m,            # RBF 함수 개수 설정
            s=s,            # RBF 폭
            regul=regul,    # 정규화 계수
            niter=niter,    # EM 알고리즘 반복 횟수
            random_state=42 # 시드 고정
        )
        
        # 학습: 확률 분포 사용
        self.gtm_modes.fit(self.prob_matrix)
        print("✅ GTM Modes 모델 학습 완료")
        return True
        
    def create_gtm_means(self, k=6, m=5, s=0.2, niter=200):
        """
        GTM (Means) 모델 생성 및 학습
        
        Args:
            k (int): GTM 격자 크기
            m (int): RBF 함수 개수
            s (float): RBF 폭
            niter (int): EM 알고리즘 반복 횟수
        """
        if self.prob_matrix is None:
            print("❌ 먼저 load_and_preprocess_data()를 실행하세요.")
            return False
            
        self.gtm_means = eGTM(
            k=k,             # GTM 격자 크기
            model="means",   # "means" 옵션 선택
            m=m,
            s=s,
            niter=niter,
            random_state=42
        )
        
        # 학습: 동일한 확률 분포 사용
        self.gtm_means.fit(self.prob_matrix)
        print("✅ GTM Means 모델 학습 완료")
        return True
        
    def visualize_gtm_modes(self):
        """
        GTM Modes 모델 시각화
        """
        if self.gtm_modes is None:
            print("❌ 먼저 create_gtm_modes()를 실행하세요.")
            return None
            
        # 2차원 투영 결과 얻기
        embedding_modes = self.gtm_modes.transform(self.prob_matrix)
        
        # 문서별 대표 토픽 라벨 할당
        dominant_topics = self.data_filtered["Dominant_Topic"].values
        dominant_topic_labels = [f"Topic {t}" for t in dominant_topics]
        
        # 시각화용 DataFrame 구성
        df_modes = pd.DataFrame({
            "x": embedding_modes[:, 0],
            "y": embedding_modes[:, 1],
            "topic_label": dominant_topic_labels
        })
        
        # 축 범위 및 눈금 설정
        _range = [-1.0, 1.0]
        _ticks = np.arange(-1.0, 1.2, 0.2)
        
        # Altair 산점도 차트 생성
        chart_modes = alt.Chart(df_modes).mark_circle(size=200).encode(
            x=alt.X(
                'x:Q',
                axis=alt.Axis(
                    title='GTM Dimension 1',
                    grid=True,
                    values=_ticks
                ),
                scale=alt.Scale(domain=_range, nice=False)
            ),
            y=alt.Y(
                'y:Q',
                axis=alt.Axis(
                    title='GTM Dimension 2',
                    grid=True,
                    values=_ticks
                ),
                scale=alt.Scale(domain=_range, nice=False)
            ),
            color=alt.Color(
                'topic_label:N',
                scale=alt.Scale(
                    domain=[
                        "Topic 0", "Topic 1", "Topic 2",
                        "Topic 3", "Topic 4", "Topic 5"
                    ],
                    range=[
                        "#8dd3c7",  # Topic 0 (연한 청록)
                        "#4eb3d3",  # Topic 1 (중간 톤 파랑)
                        "#08589e",  # Topic 2 (진한 남색)
                        "#fdb462",  # Topic 3 (연한 주황)
                        "#fb8072",  # Topic 4 (부드러운 코랄 레드)
                        "#b30000"   # Topic 5 (진한 붉은 주황)
                    ]
                ),
                legend=alt.Legend(
                    title='Patent Topics',
                    orient='right'
                )
            ),
            tooltip=[
                alt.Tooltip('topic_label:N', title='토픽'),
                alt.Tooltip('x:Q', title='X 좌표'),
                alt.Tooltip('y:Q', title='Y 좌표')
            ]
        ).properties(
            width=600,
            height=600,
            title=alt.TitleParams(
                text='Generative Topographic Mapping (Modes)',
                fontSize=16
            )
        ).configure_axis(
            labelFontSize=12,
            titleFontSize=14,
            grid=True,
            gridOpacity=0.5,
            domain=False
        ).configure_legend(
            labelFontSize=12,
            titleFontSize=14
        ).configure_view(
            stroke=None
        )
        
        return chart_modes
        
    def visualize_gtm_means(self):
        """
        GTM Means 모델 시각화
        """
        if self.gtm_means is None:
            print("❌ 먼저 create_gtm_means()를 실행하세요.")
            return None
            
        # 2차원 투영 결과 얻기
        embedding_means = self.gtm_means.transform(self.prob_matrix)
        
        # 문서별 대표 토픽 라벨 할당
        dominant_topics = self.data_filtered["Dominant_Topic"].values
        dominant_topic_labels = [f"Topic {t}" for t in dominant_topics]
        
        # 시각화용 DataFrame 구성
        df_means = pd.DataFrame({
            "x": embedding_means[:, 0],
            "y": embedding_means[:, 1],
            "topic_label": dominant_topic_labels
        })
        
        # 축 범위 및 눈금 설정
        _range = [-1.0, 1.0]
        _ticks = np.arange(-1.0, 1.2, 0.2)
        
        # Altair 산점도 차트 생성
        chart_means = alt.Chart(df_means).mark_circle(size=200).encode(
            x=alt.X(
                'x:Q',
                axis=alt.Axis(
                    title='GTM Dimension 1',
                    grid=True,
                    values=_ticks
                ),
                scale=alt.Scale(domain=_range, nice=False)
            ),
            y=alt.Y(
                'y:Q',
                axis=alt.Axis(
                    title='GTM Dimension 2',
                    grid=True,
                    values=_ticks
                ),
                scale=alt.Scale(domain=_range, nice=False)
            ),
            color=alt.Color(
                'topic_label:N',
                scale=alt.Scale(
                    domain=[
                        "Topic 0", "Topic 1", "Topic 2",
                        "Topic 3", "Topic 4", "Topic 5"
                    ],
                    range=[
                        "#8dd3c7",  # Topic 0 (연한 청록)
                        "#4eb3d3",  # Topic 1 (중간 톤 파랑)
                        "#08589e",  # Topic 2 (진한 남색)
                        "#fdb462",  # Topic 3 (연한 주황)
                        "#fb8072",  # Topic 4 (부드러운 코랄 레드)
                        "#b30000"   # Topic 5 (진한 붉은 주황)
                    ]
                ),
                legend=alt.Legend(
                    title='Patent Topics',
                    orient='right'
                )
            ),
            tooltip=[
                alt.Tooltip('topic_label:N', title='토픽'),
                alt.Tooltip('x:Q', title='X 좌표'),
                alt.Tooltip('y:Q', title='Y 좌표')
            ]
        ).properties(
            width=600,
            height=600,
            title=alt.TitleParams(
                text='Generative Topographic Mapping (Means)',
                fontSize=16
            )
        ).configure_axis(
            labelFontSize=12,
            titleFontSize=14,
            grid=True,
            gridOpacity=0.5,
            domain=False
        ).configure_legend(
            labelFontSize=12,
            titleFontSize=14
        ).configure_view(
            stroke=None
        )
        
        return chart_means
        
    def save_gtm_inverse(self, output_path=None):
        """
        GTM 모델의 격자 좌표(matY) 추출 및 저장
        
        Args:
            output_path (str): 저장할 파일 경로
        """
        if self.gtm_modes is None:
            print("❌ 먼저 create_gtm_modes()를 실행하세요.")
            return False
            
        if output_path is None:
            output_path = "GTM_inverse.csv"
            
        # GTM 모델의 격자 좌표(matY) 추출 및 저장
        matY_modes = self.gtm_modes.optimizedModel.matY
        df_matY_modes = pd.DataFrame(matY_modes).transpose()
        df_matY_modes.to_csv(output_path, index=False)
        
        print(f"GTM(Modes) matY 좌표가 '{output_path}'로 저장되었습니다.")
        return True
        
    def save_charts_as_images(self, output_dir=None, formats=['png', 'svg', 'html']):
        """
        GTM 차트를 이미지 파일로 저장
        
        Args:
            output_dir (str): 저장할 디렉토리 경로
            formats (list): 저장할 파일 형식 리스트 ['png', 'svg', 'html', 'json']
        """
        if output_dir is None:
            output_dir = "code"
            
        # 디렉토리가 없으면 생성
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        try:
            # GTM 차트 생성
            modes_chart = self.visualize_gtm_modes()
            means_chart = self.visualize_gtm_means()
            
            if modes_chart is None or means_chart is None:
                print("❌ 차트 생성에 실패했습니다.")
                return False
            
            saved_files = []
            
            for fmt in formats:
                if fmt == 'png':
                    # PNG 저장 (altair_saver 또는 selenium 필요)
                    try:
                        modes_path = os.path.join(output_dir, "gtm_modes_chart.png")
                        means_path = os.path.join(output_dir, "gtm_means_chart.png")
                        
                        modes_chart.save(modes_path)
                        means_chart.save(means_path)
                        
                        saved_files.extend([modes_path, means_path])
                        print(f"✅ PNG 파일 저장 완료: {modes_path}, {means_path}")
                    except Exception as e:
                        print(f"⚠️ PNG 저장 실패: {str(e)}")
                        print("💡 PNG 저장을 위해서는 altair_saver 또는 selenium 설치가 필요합니다.")
                
                elif fmt == 'svg':
                    # SVG 저장
                    try:
                        modes_path = os.path.join(output_dir, "gtm_modes_chart.svg")
                        means_path = os.path.join(output_dir, "gtm_means_chart.svg")
                        
                        modes_chart.save(modes_path)
                        means_chart.save(means_path)
                        
                        saved_files.extend([modes_path, means_path])
                        print(f"✅ SVG 파일 저장 완료: {modes_path}, {means_path}")
                    except Exception as e:
                        print(f"⚠️ SVG 저장 실패: {str(e)}")
                
                elif fmt == 'html':
                    # HTML 저장
                    try:
                        modes_path = os.path.join(output_dir, "gtm_modes_chart.html")  
                        means_path = os.path.join(output_dir, "gtm_means_chart.html")
                        
                        modes_chart.save(modes_path)
                        means_chart.save(means_path)
                        
                        saved_files.extend([modes_path, means_path])
                        print(f"✅ HTML 파일 저장 완료: {modes_path}, {means_path}")
                    except Exception as e:
                        print(f"⚠️ HTML 저장 실패: {str(e)}")
                
                elif fmt == 'json':
                    # JSON 저장 (차트 스펙)
                    try:
                        modes_path = os.path.join(output_dir, "gtm_modes_chart.json")
                        means_path = os.path.join(output_dir, "gtm_means_chart.json")
                        
                        modes_chart.save(modes_path)
                        means_chart.save(means_path)
                        
                        saved_files.extend([modes_path, means_path])
                        print(f"✅ JSON 파일 저장 완료: {modes_path}, {means_path}")
                    except Exception as e:
                        print(f"⚠️ JSON 저장 실패: {str(e)}")
            
            if saved_files:
                print(f"📁 총 {len(saved_files)}개 파일이 저장되었습니다.")
                return True
            else:
                print("❌ 파일 저장에 실패했습니다.")
                return False
                
        except Exception as e:
            print(f"❌ 이미지 저장 중 오류 발생: {str(e)}")
            return False
            
    def save_chart_as_matplotlib(self, output_dir=None):
        """
        GTM 차트를 matplotlib을 사용해 PNG로 저장 (Altair 대안)
        
        Args:
            output_dir (str): 저장할 디렉토리 경로
        """
        try:
            import matplotlib.pyplot as plt
            
            if output_dir is None:
                output_dir = "code"
                
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            # GTM 결과 데이터 가져오기
            if self.gtm_modes is None or self.gtm_means is None:
                print("❌ 먼저 GTM 모델을 생성하세요.")
                return False
                
            # Modes 차트
            embedding_modes = self.gtm_modes.transform(self.prob_matrix)
            dominant_topics = self.data_filtered["Dominant_Topic"].values
            
            plt.figure(figsize=(10, 8))
            scatter = plt.scatter(embedding_modes[:, 0], embedding_modes[:, 1], 
                                c=dominant_topics, cmap='tab10', s=50, alpha=0.7)
            plt.colorbar(scatter, label='Topic')
            plt.xlabel('GTM Dimension 1')
            plt.ylabel('GTM Dimension 2')
            plt.title('Generative Topographic Mapping (Modes)')
            plt.grid(True, alpha=0.3)
            
            modes_path = os.path.join(output_dir, "gtm_modes_matplotlib.png")
            plt.savefig(modes_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            # Means 차트
            embedding_means = self.gtm_means.transform(self.prob_matrix)
            
            plt.figure(figsize=(10, 8))
            scatter = plt.scatter(embedding_means[:, 0], embedding_means[:, 1], 
                                c=dominant_topics, cmap='tab10', s=50, alpha=0.7)
            plt.colorbar(scatter, label='Topic')
            plt.xlabel('GTM Dimension 1')
            plt.ylabel('GTM Dimension 2')
            plt.title('Generative Topographic Mapping (Means)')
            plt.grid(True, alpha=0.3)
            
            means_path = os.path.join(output_dir, "gtm_means_matplotlib.png")
            plt.savefig(means_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"✅ Matplotlib PNG 저장 완료: {modes_path}, {means_path}")
            return True
            
        except ImportError:
            print("❌ matplotlib 라이브러리가 필요합니다.")
            return False
        except Exception as e:
            print(f"❌ Matplotlib 저장 중 오류 발생: {str(e)}")
            return False
        
    def run_full_analysis(self, save_images=True, image_formats=['html', 'png']):
        """
        전체 GTM 분석 파이프라인 실행
        
        Args:
            save_images (bool): 이미지 파일 저장 여부
            image_formats (list): 저장할 이미지 형식
        
        Returns:
            tuple: (modes_chart, means_chart) Altair 차트 객체들
        """
        try:
            # 1. 데이터 로드 및 전처리
            if not self.load_and_preprocess_data():
                return None, None
            
            # 2. GTM 모델 생성 및 학습
            self.create_gtm_modes()
            self.create_gtm_means()
            
            # 3. 시각화 생성
            modes_chart = self.visualize_gtm_modes()
            means_chart = self.visualize_gtm_means()
            
            # 4. GTM 역변환 좌표 저장
            self.save_gtm_inverse()
            
            # 5. 이미지 파일 저장 (선택적)
            if save_images:
                print("📸 GTM 차트 이미지 저장 중...")
                self.save_charts_as_images(formats=image_formats)
                
                # matplotlib 백업 저장도 시도
                try:
                    self.save_chart_as_matplotlib()
                except:
                    pass  # matplotlib 저장 실패해도 계속 진행
            
            print("✅ GTM 분석 완료!")
            return modes_chart, means_chart
            
        except Exception as e:
            print(f"❌ GTM 분석 중 오류 발생: {str(e)}")
            return None, None

if __name__ == "__main__":
    # 테스트 실행
    gtm_analyzer = Step4_2_GTM()
    modes_chart, means_chart = gtm_analyzer.run_full_analysis()
    
    if modes_chart and means_chart:
        print("GTM Modes 차트:")
        print(modes_chart.display())
        print("\nGTM Means 차트:")
        print(means_chart.display())