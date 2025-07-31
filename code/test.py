import streamlit as st
import json
import os
import glob
from datetime import datetime
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from PIL import Image
import pandas as pd
import time
import sys
import importlib

# 한글 파일명 import 처리
try:
    step1_module = importlib.import_module('step1_특허식')
    step2_module = importlib.import_module('step2_크롤링')
    step3_module = importlib.import_module('step3_필터링')
    step3_5_module = importlib.import_module('step3_5_특허그래프')
    step4_module = importlib.import_module('step4_벌토픽')
    step5_module = importlib.import_module('step5_보고서작성')
    
    Step1 = step1_module.Step1
    Step2 = step2_module.Step2
    Step3 = step3_module.Step3
    Step3_5 = step3_5_module.Step3_5
    Step4 = step4_module.Step4
    Step5 = step5_module.Step5
except ImportError as e:
    st.error(f"모듈 import 오류: {e}")
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="AI 특허 분석 및 기술 보고서 생성 시스템",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    .main-title {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .step-container {
        border: 2px solid #e1e5e9;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #6fa1aa;
    }
    .step-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
    }
    
    /* 다크모드 대응 */
    @media (prefers-color-scheme: dark) {
        .step-container {
            border: 2px solid #4a5568;
            background-color: #2d3748;
        }
        .step-title {
            color: #e2e8f0;
        }
        .step-container p {
            color: #cbd5e0;
        }
    }
    
    /* Streamlit 다크 테마 적용 시 */
    [data-testid="stAppViewContainer"][data-theme="dark"] .step-container,
    .stApp[data-theme="dark"] .step-container {
        border: 2px solid #4a5568;
        background-color: #2d3748;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .step-title,
    .stApp[data-theme="dark"] .step-title {
        color: #e2e8f0;
    }
    [data-testid="stAppViewContainer"][data-theme="dark"] .step-container p,
    .stApp[data-theme="dark"] .step-container p {
        color: #cbd5e0;
    }
    .progress-container {
        border: 2px solid #17a2b8;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background-color: #004c8e;
    }
</style>
""", unsafe_allow_html=True)

# 세션 상태 초기화
if "step_progress" not in st.session_state:
    st.session_state.step_progress = 0
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
if "topic_results" not in st.session_state:
    st.session_state.topic_results = None
if "keyword_input" not in st.session_state:
    st.session_state.keyword_input = ""
if "waiting_for_date_input" not in st.session_state:
    st.session_state.waiting_for_date_input = False
if "date_filtered" not in st.session_state:
    st.session_state.date_filtered = False

def update_progress(step, message):
    """진행 상황 업데이트"""
    progress_data = {
        "stage": f"Step {step}",
        "current": step,
        "total": 6,
        "message": message
    }
    with open("progress.json", "w", encoding="utf-8") as f:
        json.dump(progress_data, f, ensure_ascii=False)
    
    # step_progress는 숫자만 저장 (3_5는 3으로 처리)
    if step == "3_5":
        st.session_state.step_progress = 3
    else:
        st.session_state.step_progress = step

def filter_data_by_date(start_year, end_year):
    """날짜 범위로 특허 데이터 필터링"""
    try:
        df = pd.read_csv("./extract_end.csv")
        
        # 출원일 처리
        df["출원일"] = df["출원일"].astype(str).str.strip()
        df["출원연도"] = pd.to_datetime(
            df["출원일"], errors="coerce", infer_datetime_format=True
        ).dt.year
        
        # 날짜 범위 필터링
        filtered_df = df[(df["출원연도"] >= start_year) & (df["출원연도"] <= end_year)]
        
        # 필터링된 데이터 저장
        filtered_df.to_csv("./extract_end.csv", index=False)
        
        print(f"📅 날짜 필터링 완료: {start_year}-{end_year}, {len(filtered_df)}건 남음")
        return len(filtered_df)
        
    except Exception as e:
        print(f"날짜 필터링 중 오류: {str(e)}")
        return 0

def run_analysis_pipeline(keyword):
    """실시간 progress bar가 적용된 분석 파이프라인"""
    
    # 메인 진행률 표시 컨테이너
    with st.container():
        st.markdown("## 🔄 분석 진행 중...")
        
        # Progress bar와 상태 표시
        main_progress = st.progress(0.0)
        status_container = st.empty()
        detail_container = st.empty()
        
        # 전체 진행률 (각 단계별 가중치) - step3_5가 추가되어 6단계로 변경
        step_weights = {1: 0.1, 2: 0.25, 3: 0.15, "3_5": 0.1, 4: 0.3, 5: 0.1}
        base_progress = 0.0
        
        # Step1에서 생성된 키워드를 저장할 변수
        generated_keywords = None
    
    def monitor_progress_file(step_num, step_name, icon):
        """progress.json 파일을 모니터링하여 실시간 업데이트"""
        nonlocal base_progress
        
        status_container.info(f"{icon} Step {step_num}: {step_name} 중...")
        
        # progress.json 파일 모니터링
        import time
        
        while True:
            try:
                if os.path.exists("progress.json"):
                    with open("progress.json", "r", encoding="utf-8") as f:
                        progress_data = json.load(f)
                    
                    current = progress_data.get("current", 0)
                    total = progress_data.get("total", 1)
                    message = progress_data.get("message", "")
                    
                    # 진행률 계산 및 업데이트
                    if total > 0:
                        step_progress = min(current / total, 1.0)
                        
                        # 전체 진행률 업데이트
                        overall_progress = base_progress + (step_weights[step_num] * step_progress)
                        main_progress.progress(overall_progress)
                        
                        # 상세 정보 표시
                        detail_container.write(f"📋 {message}")
                        
                        # 단계 완료 확인
                        if step_progress >= 1.0:
                            break
                            
                    time.sleep(0.1)  # 0.1초마다 체크
                else:
                    time.sleep(0.5)
            except:
                time.sleep(0.5)
    
    try:
        import threading
        
        # Step 1: 특허식 생성
        status_container.info("🔍 Step 1: 키워드 분석 및 특허식 생성 중...")
        update_progress(1, f"키워드 '{keyword}'로 특허식 생성 중...")
        
        s1 = Step1()
        sentence = s1.make(keyword)
        
        # Step1에서 생성된 키워드 리스트 추출 (문자열에서 리스트로 변환)
        import ast
        try:
            generated_keywords = ast.literal_eval(sentence)
        except:
            # 파싱에 실패하면 기본 키워드 사용
            generated_keywords =[] #["자율주행", "로봇", "배터리", "전기차", "AI", "인공지능"]
        
        # 세션 상태에 키워드 저장
        st.session_state.generated_keywords = generated_keywords
        
        base_progress = step_weights[1]
        main_progress.progress(base_progress)
        status_container.success("✅ Step 1 완료: 특허식 생성 완료")
        detail_container.write(f"✅ 생성된 특허식: {sentence}")
        time.sleep(0.5)
        
        # Step 2: 특허 크롤링
        update_progress(2, "특허 크롤링 중...")
        
        # 별도 스레드에서 progress 모니터링
        progress_thread = threading.Thread(
            target=monitor_progress_file, 
            args=(2, "KIPRIS 특허 데이터 크롤링", "📊")
        )
        progress_thread.daemon = True
        progress_thread.start()
        
        s2 = Step2()
        s2.cra(sentence)
        
        progress_thread.join(timeout=1)
        base_progress += step_weights[2]
        main_progress.progress(base_progress)
        status_container.success("✅ Step 2 완료: 특허 데이터 수집 완료")
        time.sleep(0.5)
        
        # Step 3: 데이터 필터링
        update_progress(3, "특허 필터링 중...")
        
        progress_thread = threading.Thread(
            target=monitor_progress_file, 
            args=(3, "유사도 기반 특허 필터링", "🔧")
        )
        progress_thread.daemon = True
        progress_thread.start()
        
        s3 = Step3()
        s3.filter()
        
        progress_thread.join(timeout=1)
        base_progress += step_weights[3]
        main_progress.progress(base_progress)
        status_container.success("✅ Step 3 완료: 데이터 필터링 완료")
        time.sleep(0.5)
        
        # Step 3.5: 특허 그래프 표시
        update_progress("3_5", "특허 그래프 생성 중...")
        status_container.info("📊 Step 3.5: 특허 연도별 그래프 생성 중...")
        
        # Step3_5 클래스 사용
        try:
            s3_5 = Step3_5()
            print(f"Step3_5 클래스 생성 완료, 키워드: {generated_keywords}")
            graph_data = s3_5.generate_graph(generated_keywords)
            print(f"Step3_5 그래프 데이터 생성 완료: {graph_data is not None}")
            
            # 그래프 데이터를 세션 상태에 저장
            st.session_state.graph_data = graph_data
        except Exception as e:
            print(f"Step3_5 실행 중 오류: {str(e)}")
            import traceback
            traceback.print_exc()
            # 오류가 발생해도 계속 진행
            st.session_state.graph_data = None
        
        base_progress += step_weights["3_5"]
        main_progress.progress(base_progress)
        status_container.success("✅ Step 3.5 완료: 특허 그래프 생성 완료")
        detail_container.write("✅ 연도별 특허 출원 동향 그래프가 생성되었습니다.")
        
        # Step 3.5 완료 후 사용자 날짜 입력 대기 상태로 전환
        st.session_state.waiting_for_date_input = True
        status_container.info("⏸️ 날짜 범위 입력을 기다리는 중...")
        detail_container.write("📅 아래에서 분석할 날짜 범위를 선택하고 '계속 진행' 버튼을 클릭하세요.")
        return None  # 여기서 파이프라인 일시정지
        
    except Exception as e:
        main_progress.progress(0.0)
        status_container.error(f"❌ 분석 중 오류 발생")
        detail_container.error(f"오류 내용: {str(e)}")
        st.error(f"❌ 분석 중 오류 발생: {str(e)}")
        return None

def continue_analysis_from_step4():
    """Step4부터 분석 재개"""
    
    # 메인 진행률 표시 컨테이너
    with st.container():
        st.markdown("## 🔄 분석 재개 중...")
        
        # Progress bar와 상태 표시
        main_progress = st.progress(0.6)  # Step3_5까지 완료된 상태에서 시작
        status_container = st.empty()
        detail_container = st.empty()
        
        step_weights = {1: 0.1, 2: 0.25, 3: 0.15, "3_5": 0.1, 4: 0.3, 5: 0.1}
        base_progress = step_weights[1] + step_weights[2] + step_weights[3] + step_weights["3_5"]
        
    def monitor_progress_file(step_num, step_name, icon):
        """progress.json 파일을 모니터링하여 실시간 업데이트"""
        nonlocal base_progress
        
        status_container.info(f"{icon} Step {step_num}: {step_name} 중...")
        
        # progress.json 파일 모니터링
        import time
        
        while True:
            try:
                if os.path.exists("progress.json"):
                    with open("progress.json", "r", encoding="utf-8") as f:
                        progress_data = json.load(f)
                    
                    current = progress_data.get("current", 0)
                    total = progress_data.get("total", 1)
                    message = progress_data.get("message", "")
                    
                    # 진행률 계산 및 업데이트
                    if total > 0:
                        step_progress = min(current / total, 1.0)
                        
                        # 전체 진행률 업데이트
                        overall_progress = base_progress + (step_weights[step_num] * step_progress)
                        main_progress.progress(overall_progress)
                        
                        # 상세 정보 표시
                        detail_container.write(f"📋 {message}")
                        
                        # 단계 완료 확인
                        if step_progress >= 1.0:
                            break
                            
                    time.sleep(0.1)  # 0.1초마다 체크
                else:
                    time.sleep(0.5)
            except:
                time.sleep(0.5)
    
    try:
        import threading
        
        # Step 4: 토픽 모델링
        update_progress(4, "토픽 추출 및 시각화 중...")
        
        progress_thread = threading.Thread(
            target=monitor_progress_file, 
            args=(4, "BERTopic 토픽 모델링 및 시각화", "🤖")
        )
        progress_thread.daemon = True
        progress_thread.start()
        
        s4 = Step4()
        topic_list = s4.ber()
        
        # 토픽 결과 검증
        if not topic_list or not isinstance(topic_list, dict):
            main_progress.progress(0.9)
            status_container.error("❌ Step 4 실패: 토픽 추출 중 오류 발생")
            detail_container.error("토픽 모델링에 실패했습니다. 데이터를 확인해주세요.")
            return None
            
        progress_thread.join(timeout=1)
        base_progress += step_weights[4]
        main_progress.progress(base_progress)
        status_container.success("✅ Step 4 완료: 토픽 추출 및 시각화 완료")
        detail_container.write(f"✅ {len(topic_list)}개의 주요 토픽을 발견했습니다.")
        time.sleep(0.5)
        
        # Step 5: 보고서 생성
        update_progress(5, "보고서 작성 중...")
        
        progress_thread = threading.Thread(
            target=monitor_progress_file, 
            args=(5, "AI 기반 기술 보고서 작성", "📝")
        )
        progress_thread.daemon = True
        progress_thread.start()
        
        s5 = Step5()
        s5.last(topic_list)
        
        progress_thread.join(timeout=1)
        main_progress.progress(1.0)
        status_container.success("🎉 모든 분석이 완료되었습니다!")
        detail_container.write("🎊 AI 기술 보고서 생성이 성공적으로 완료되었습니다!")
        
        # 결과 저장
        st.session_state.topic_results = topic_list
        st.session_state.analysis_complete = True
        st.session_state.waiting_for_date_input = False
        
        return topic_list
        
    except Exception as e:
        main_progress.progress(0.6)
        status_container.error(f"❌ 분석 중 오류 발생")
        detail_container.error(f"오류 내용: {str(e)}")
        st.error(f"❌ 분석 중 오류 발생: {str(e)}")
        return None

def display_topic_visualization():
    """토픽 시각화 결과 표시"""
    st.subheader("📊 토픽 분석 시각화 결과")
    
    # UMAP 이미지 표시
    st.markdown("### 🗺️ UMAP 2D 토픽 분포")
    umap_image_path = "umap2d_topics_custom_color_pret.png"
    if os.path.exists(umap_image_path):
        image = Image.open(umap_image_path)
        st.image(image, caption="UMAP 2D 문서 임베딩과 BERTopic 토픽 분포", use_column_width=True)
    else:
        st.warning("UMAP 시각화 이미지를 찾을 수 없습니다.")
    
    # Topic Words Chart 이미지 표시
    st.markdown("### 📈 토픽별 주요 키워드")
    topic_words_image_path = "./topic_words_chart.png"
    if os.path.exists(topic_words_image_path):
        image2 = Image.open(topic_words_image_path)
        st.image(image2, caption="토픽별 상위 12개 주요 키워드 분포", use_column_width=True)
    else:
        st.info("토픽 키워드 차트 이미지를 찾을 수 없습니다.")

def display_patent_graph():
    """특허 연도별 그래프 표시 (step3_5 내용)"""
    st.subheader("📊 키워드별 연도별 특허 출원 동향")
    st.write("`검색 키워드` 컬럼에서 필터링 후 연도별 출원 건수를 표시합니다.")
    
    # 세션 상태에서 그래프 데이터 가져오기
    if hasattr(st.session_state, 'graph_data') and st.session_state.graph_data is not None:
        final_df = st.session_state.graph_data
        
        # 키워드별 건수 표시
        if hasattr(st.session_state, 'generated_keywords') and st.session_state.generated_keywords:
            try:
                df = pd.read_csv("./extract_end.csv")
                for kw in st.session_state.generated_keywords:
                    mask = df["검색 키워드"].astype(str).str.contains(kw, case=False, na=False)
                    count = mask.sum()
                    st.write(f"**{kw}** → {count}건")
            except:
                pass
        
        # 📊 라인 차트 출력
        st.line_chart(final_df, use_container_width=True)
    else:
        # 그래프 데이터가 없으면 Step3_5 클래스로 새로 생성
        try:
            s3_5 = Step3_5()
            keywords = st.session_state.generated_keywords if hasattr(st.session_state, 'generated_keywords') else None
            final_df = s3_5.generate_graph(keywords)
            
            if final_df is not None:
                st.line_chart(final_df, use_container_width=True)
            else:
                st.error("❌ 그래프 데이터를 생성할 수 없습니다.")
        except Exception as e:
            st.error(f"그래프 생성 중 오류 발생: {str(e)}")

def display_generated_reports():
    """생성된 보고서 목록 및 내용 표시"""
    st.subheader("📋 생성된 기술 보고서")
    
    reports_dir = "generated_reports"
    
    # 상대 경로와 절대 경로 모두 확인
    possible_paths = [
        reports_dir,
        f"./code/{reports_dir}",
        f"/Users/shinseungmin/Documents/벌토픽_전체코드/code/{reports_dir}",
        f"code/{reports_dir}"
    ]
    
    found_reports_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            found_reports_dir = path
            break
    
    if not found_reports_dir:
        st.warning("📋 기술 보고서가 아직 생성되지 않았습니다.")
        st.info("💡 토픽 분석을 완료하면 자동으로 AI 기술 보고서가 생성됩니다.")
        return
    
    report_files = glob.glob(os.path.join(found_reports_dir, "*.md"))
    
    if not report_files:
        st.warning("📋 기술 보고서가 아직 생성되지 않았습니다.")
        st.info("💡 토픽 분석을 완료하면 자동으로 AI 기술 보고서가 생성됩니다.")
        return
    
    # 보고서 선택
    report_names = [os.path.basename(f) for f in report_files]
    selected_report = st.selectbox("보고서 선택:", report_names)
    
    if selected_report:
        report_path = os.path.join(found_reports_dir, selected_report)
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            st.markdown(content)
        except Exception as e:
            st.error(f"보고서를 읽는 중 오류 발생: {str(e)}")

def display_topic_results():
    """토픽 분석 결과 표시"""
    if st.session_state.topic_results:
        st.subheader("🔍 토픽 분석 결과")
        
        for topic_id, words in st.session_state.topic_results.items():
            # topic_id가 문자열일 수 있으므로 int로 변환 후 처리
            try:
                topic_num = int(topic_id)
                display_topic_id = topic_num if topic_num >= 0 else "Noise"
            except (ValueError, TypeError):
                display_topic_id = str(topic_id)
                
            with st.expander(f"Topic {display_topic_id}"):
                st.write("**주요 키워드:**")
                if isinstance(words, list):
                    st.write(", ".join(words[:10]))  # 상위 10개 키워드만 표시
                else:
                    st.write(str(words))
    else:
        st.warning("🔍 토픽 분석이 아직 완료되지 않았습니다.")
        st.info("💡 **완전한 토픽 분석을 위해서는** 위의 특허 동향 그래프를 확인한 후, 원하는 날짜 범위를 선택하고 **'🚀 날짜 범위 적용 후 계속 진행'** 버튼을 클릭하세요.")
        st.markdown("""
        ### 📋 토픽 분석에서 확인할 수 있는 내용:
        - 🎯 특허 데이터에서 추출된 주요 기술 주제들
        - 🔍 각 토픽별 핵심 키워드 및 기술 용어
        - 📊 토픽별 문서 분포 및 중요도
        - 🧠 AI 기반 의미론적 클러스터링 결과
        """)

def main():
    # 멋진 배너 디자인을 위한 CSS
    st.markdown("""
    <style>
    .main > div {
        padding-top: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 100% !important;
    }
    .stApp > header {
        background-color: transparent;
        height: 0px;
        display: none;
    }
    .stApp {
        padding-top: 0rem !important;
    }
    /* ChatGPT 스타일 사이드바 */
    .css-1d391kg {
        width: 320px !important;
    }
    section[data-testid="stSidebar"] {
        width: 320px !important;
        background: #1f2937 !important;
        border-right: 1px solid #374151 !important;
    }
    .css-1cypcdb {
        width: 320px !important;
    }
    
    /* 사이드바 컨텐츠 스타일링 */
    section[data-testid="stSidebar"] > div {
        background: transparent !important;
        padding: 1rem !important;
    }
    
    /* 사이드바 헤더 스타일 */
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #f9fafb !important;
        font-weight: 600 !important;
    }
    
    /* 사이드바 텍스트 스타일 */
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] label {
        color: #d1d5db !important;
    }
    
    /* 입력 필드 컨테이너 스타일 */
    .sidebar-input-container {
        background: #374151 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        border: 1px solid #4b5563 !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
    }
    
    /* 호버 효과 */
    .sidebar-input-container:hover {
        background: #4b5563 !important;
        border-color: #6b7280 !important;
    }
    
    /* 텍스트 입력 필드 스타일 */
    section[data-testid="stSidebar"] .stTextInput > div > div > input {
        background: #2d3748 !important;
        border: 1px solid #4a5568 !important;
        border-radius: 8px !important;
        color: #f7fafc !important;
        font-size: 0.95rem !important;
        font-weight: 400 !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    
    section[data-testid="stSidebar"] .stTextInput > div > div > input:focus {
        background: #2d3748 !important;
        border: 1px solid #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1) !important;
        outline: none !important;
        transform: none !important;
    }
    
    section[data-testid="stSidebar"] .stTextInput > div > div > input::placeholder {
        color: #9ca3af !important;
        opacity: 1 !important;
    }
    
    /* 버튼 스타일 */
    section[data-testid="stSidebar"] .stButton > button {
        background: #10b981 !important;
        border: none !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 500 !important;
        padding: 0.75rem 1rem !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
        width: 100% !important;
        text-transform: none !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: #059669 !important;
        transform: none !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15) !important;
    }
    
    section[data-testid="stSidebar"] .stButton > button:active {
        transform: translateY(1px) !important;
    }
    
    /* 비활성화된 버튼 스타일 */
    section[data-testid="stSidebar"] .stButton > button:disabled {
        background: #6b7280 !important;
        color: #9ca3af !important;
        box-shadow: none !important;
        transform: none !important;
    }
    
    /* 진행률 표시 카드 */
    .sidebar-progress-card {
        background: #374151 !important;
        border-radius: 12px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        border: 1px solid #4b5563 !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.2s ease !important;
    }
    
    .sidebar-progress-card:hover {
        background: #4b5563 !important;
        border-color: #6b7280 !important;
        transform: none !important;
    }
    
    /* 성공 메시지 스타일 */
    section[data-testid="stSidebar"] .stSuccess {
        background: rgba(16, 185, 129, 0.1) !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
        border-radius: 8px !important;
        box-shadow: none !important;
    }
    
    section[data-testid="stSidebar"] .stSuccess > div {
        color: #10b981 !important;
        font-weight: 500 !important;
    }
    
    /* 진행률 바 스타일 */
    section[data-testid="stSidebar"] .stProgress > div > div {
        background: #4b5563 !important;
        border-radius: 4px !important;
        box-shadow: none !important;
    }
    
    section[data-testid="stSidebar"] .stProgress > div > div > div {
        background: #10b981 !important;
        border-radius: 4px !important;
        box-shadow: none !important;
    }
    
    /* 멋진 배너 컨테이너 */
    .banner-container {
        position: relative;
        width: 100%;
        height: 300px;
        margin: -4rem 0 2rem 0;
        border-radius: 15px;
        overflow: hidden;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .banner-image {
        width: 100%;
        height: 100%;
        object-fit: cover;
        border-radius: 15px;
        transition: transform 0.3s ease;
    }
    
    .banner-overlay {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(
            135deg, 
            rgba(0, 0, 0, 0.3) 0%, 
            rgba(0, 0, 0, 0.1) 50%, 
            rgba(0, 0, 0, 0.2) 100%
        );
        border-radius: 15px;
    }
    
    .banner-title {
        position: absolute;
        top: -30px;
        left: 50%;
        transform: translateX(-50%);
        text-align: center;
        color: #1f77b4;
        font-size: 2.5rem;
        font-weight: bold;
        line-height: 1;
        z-index: 10;
        padding: 10px;
        white-space: nowrap;
        width: max-content;
    }
    
    /* 호버 효과 */
    .banner-container:hover .banner-image {
        transform: scale(1.02);
    }
    
    /* 메인 타이틀 숨기기 */
    .main-title {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 상단 배경 이미지
    possible_paths = ["./top4.png", "top4.png", "../top4.png", "code/top4.png"]
    
    for path in possible_paths:
        if os.path.exists(path):
            top_image = Image.open(path)
            
            # HTML로 멋진 배너 생성
            import base64
            from io import BytesIO
            
            # 이미지를 base64로 인코딩
            buffer = BytesIO()
            top_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            st.markdown(f"""
            <div class="banner-container">
                <img src="data:image/png;base64,{img_str}" alt="Banner" class="banner-image">
                <div class="banner-overlay"></div>
            </div>
            """, unsafe_allow_html=True)
            break
    
    # 메인 타이틀
    st.markdown('<h1 class="main-title">🔬 AI 특허 분석 및 기술 보고서 생성 시스템</h1>', unsafe_allow_html=True)
    
    # 사이드바
    with st.sidebar:
        st.header("🔍 키워드 분석 시작")
        
        # 키워드 입력
        keyword = st.text_input(
            "🔍 분석할 기술 키워드를 입력하세요:",
            value=st.session_state.keyword_input,
            placeholder="예: 자율주행 로봇, 인공지능, 블록체인",
            help="키워드를 명확하게 입력하면 더 정확한 분석 결과를 얻을 수 있습니다."
        )
        
        # 분석 시작 버튼
        if st.button("🚀 분석 시작", type="primary", disabled=not keyword):
            st.session_state.keyword_input = keyword
            st.session_state.analysis_complete = False
            st.session_state.topic_results = None
            st.session_state.step_progress = 0
            st.session_state.waiting_for_date_input = False
            st.session_state.date_filtered = False
            
            # 분석 실행
            with st.spinner("분석을 진행 중입니다..."):
                run_analysis_pipeline(keyword)
        
        # 진행 상황 표시 (분석 완료되지 않았을 때만, 단 날짜 입력 대기 중일 때는 숨김)
        if st.session_state.step_progress > 0 and not st.session_state.analysis_complete and not st.session_state.waiting_for_date_input:
            st.markdown('<div class="sidebar-progress-card">', unsafe_allow_html=True)
            st.markdown("### 📈 진행 상황")
            
            progress_value = st.session_state.step_progress / 5
            st.progress(progress_value)
            st.write(f"Step {st.session_state.step_progress}/5 완료")
            st.markdown('</div>', unsafe_allow_html=True)
        
        # 분석 완료 후 옵션
        if st.session_state.analysis_complete:
            if hasattr(st.session_state, 'selected_date_range') and st.session_state.selected_date_range:
                date_info = st.session_state.selected_date_range
                st.success(f"✅ 맞춤 분석 완료!\n📅 {date_info['start_year']}-{date_info['end_year']} • {date_info['filtered_count']}건")
            else:
                st.success("✅ 분석 완료!")
        
    
    # 메인 컨텐츠 영역
    if not st.session_state.analysis_complete and st.session_state.step_progress == 0:
        # 첫 화면 - 히어로 섹션
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0 3rem 0;">
            <h1 style="font-size: 3rem; font-weight: 700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;">
                AI 특허 분석 플랫폼
            </h1>
            <p style="font-size: 1.1rem; color: #64748b; line-height: 1.6; max-width: 600px; margin: 0 auto;">
                최첨단 AI 기술로 특허 데이터를 분석하고<br>전문적인 인사이트가 담긴 기술 보고서를 자동 생성합니다
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 3개 열로 나눠서 기능 소개
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem;">📅 맞춤형 날짜 선택</h3>
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">그래프 확인 후 원하는 기간만<br>선택하여 정밀 분석</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem;">📊 실시간 트렌드 분석</h3>
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">연도별 특허 동향을 시각화하고<br>핵심 패턴 파악</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center; height: 160px; display: flex; flex-direction: column; justify-content: center;">
                <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem;">🎯 정밀한 인사이트</h3>
                <p style="margin: 0; font-size: 0.9rem; line-height: 1.4;">선택된 기간의 데이터만으로<br>더 정확한 토픽 추출</p>
            </div>
            """, unsafe_allow_html=True)
        
        # CTA 버튼 - 중앙 정렬
        st.markdown("""
        <div style="text-align: center; margin: 3rem 0;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1rem 2rem; border-radius: 50px; display: inline-block; box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);">
                <p style="color: white; font-size: 1.1rem; font-weight: 600; margin: 0;">
                    🚀 왼쪽에서 키워드를 입력하고 분석을 시작하세요
                </p>
            </div>
            <p style="color: #94a3b8; margin-top: 1rem; font-size: 0.9rem;">예시: 자율주행, 인공지능, 블록체인, 양자컴퓨팅</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 상세 기능 소개 섹션
        st.markdown("""
        <div style="margin: 6rem 0 4rem 0; padding-top: 4rem; border-top: 1px solid #e2e8f0;">
            <h2 style="text-align: center; font-size: 2.5rem; font-weight: 700; color: #1e293b; margin-bottom: 1rem;">✨ 상세 기능 소개</h2>
            <p style="text-align: center; font-size: 1.1rem; color: #64748b; margin-bottom: 4rem; max-width: 700px; margin-left: auto; margin-right: auto;">
                6단계 인터랙티브 AI 분석 프로세스로 사용자가 직접 날짜를 선택하여<br>맞춤형 특허 분석 보고서를 생성합니다
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 기능 카드들을 2x3 그리드로 배치
        col1, col2 = st.columns(2, gap="large")
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 20px; color: white; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3); transform: translateY(0); transition: all 0.3s ease;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔍</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: white;">스마트 특허식 생성</h3>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5; color: white;">GPT-3.5 기반으로 입력 키워드를 분석하여 KIPRIS 검색에 최적화된 특허식을 자동 생성합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 2rem; border-radius: 20px; color: white; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(240, 147, 251, 0.3);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🔧</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: white;">AI 데이터 필터링</h3>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5; color: white;">OpenAI 임베딩을 활용한 의미론적 유사도 분석으로 관련성 높은 특허만 선별합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); padding: 2rem; border-radius: 20px; color: white; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(255, 154, 158, 0.3);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: white;">인터랙티브 트렌드 분석</h3>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5; color: white;">연도별 특허 동향 그래프를 보고 사용자가 직접 분석 기간을 선택할 수 있습니다.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 2rem; border-radius: 20px; color: white; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(250, 112, 154, 0.3);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📈</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: white;">대용량 특허 크롤링</h3>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5; color: white;">KIPRIS API를 통해 관련 특허 데이터를 체계적으로 수집하고 구조화합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 2rem; border-radius: 20px; color: #333; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(168, 237, 234, 0.3);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: #333;">맞춤형 토픽 모델링</h3>
                <p style="font-size: 1rem; opacity: 0.8; line-height: 1.5; color: #333;">선택된 기간의 특허만으로 BERTopic 분석을 수행하여 더 정밀한 토픽을 추출합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 2rem; border-radius: 20px; color: white; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(79, 172, 254, 0.3);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📝</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: white;">전문 보고서 생성</h3>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5; color: white;">GPT-4를 활용하여 선별된 데이터를 바탕으로 전문적인 기술 보고서를 자동 작성합니다.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # 시작하기 섹션
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 3rem 2rem; border-radius: 25px; text-align: center; margin: 4rem 0; color: white; box-shadow: 0 15px 35px rgba(102, 126, 234, 0.3);">
            <h2 style="font-size: 2rem; font-weight: 600; margin-bottom: 1rem; color: white;">🚀 지금 시작하세요</h2>
            <p style="font-size: 1.2rem; opacity: 0.9; margin-bottom: 2rem; color: white;">왼쪽 사이드바에서 분석하고 싶은 기술 키워드를 입력하고 '분석 시작' 버튼을 클릭하세요</p>
            <div style="background: rgba(255,255,255,0.2); padding: 1rem; border-radius: 15px; backdrop-filter: blur(10px);">
                <p style="font-size: 1rem; margin: 0; color: white; opacity: 0.9;">💡 예시: 자율주행 로봇, 인공지능, 블록체인, 양자컴퓨팅</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 분석 프로세스 플로우
        st.markdown("""
        <div style="margin: 4rem 0;">
            <h2 style="text-align: center; font-size: 2.2rem; font-weight: 600; color: #1e293b; margin-bottom: 3rem;">⚡ 인터랙티브 분석 프로세스</h2>
            <p style="text-align: center; font-size: 1rem; color: #64748b; margin-bottom: 3rem;">사용자가 직접 참여하는 맞춤형 6단계 분석</p>
        </div>
        """, unsafe_allow_html=True)
        
        # 6단계 프로세스를 2행으로 배치
        # 첫 번째 행: Step 1-3
        col1, col2, col3 = st.columns(3, gap="medium")
        processes_row1 = [
            {"step": "01", "title": "특허식 생성", "desc": "AI 키워드 분석", "icon": "🔍", "color": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"},
            {"step": "02", "title": "데이터 크롤링", "desc": "KIPRIS API 연동", "icon": "📈", "color": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"},
            {"step": "03", "title": "스마트 필터링", "desc": "AI 임베딩 분석", "icon": "🔧", "color": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"}
        ]
        
        columns = [col1, col2, col3]
        
        for i, (col, process) in enumerate(zip(columns, processes_row1)):
            with col:
                st.markdown(f"""
                <div style="text-align: center; position: relative;">
                    <div style="background: {process['color']}; width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 1rem auto; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 25px rgba(0,0,0,0.15); position: relative;">
                        <span style="font-size: 2rem;">{process['icon']}</span>
                        <div style="position: absolute; top: -10px; right: -10px; background: #1e293b; color: white; width: 25px; height: 25px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600;">{process['step']}</div>
                    </div>
                    <h4 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">{process['title']}</h4>
                    <p style="font-size: 0.85rem; color: #64748b; margin: 0;">{process['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 화살표 추가 (마지막 단계 제외)
                if i < len(processes_row1) - 1:
                    st.markdown("""
                    <div style="text-align: center; margin: 1rem 0;">
                        <span style="font-size: 1.5rem; color: #cbd5e1;">→</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # 두 번째 행: Step 3.5-5 + 사용자 참여 단계
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0;">
            <span style="font-size: 2rem; color: #cbd5e1;">↓</span>
        </div>
        """, unsafe_allow_html=True)
        
        col4, col5, col6 = st.columns(3, gap="medium")
        processes_row2 = [
            {"step": "3.5", "title": "트렌드 분석", "desc": "📅 사용자 날짜 선택", "icon": "📊", "color": "linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%)"},
            {"step": "04", "title": "맞춤 토픽 모델링", "desc": "선택된 기간 분석", "icon": "🤖", "color": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"},
            {"step": "05", "title": "전문 보고서", "desc": "GPT-4 자동 작성", "icon": "📝", "color": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"}
        ]
        
        columns2 = [col4, col5, col6]
        
        for i, (col, process) in enumerate(zip(columns2, processes_row2)):
            with col:
                special_style = "border: 3px solid #ff6b6b; animation: pulse 2s infinite;" if process['step'] == "3.5" else ""
                st.markdown(f"""
                <div style="text-align: center; position: relative;">
                    <div style="background: {process['color']}; width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 1rem auto; display: flex; align-items: center; justify-content: center; box-shadow: 0 8px 25px rgba(0,0,0,0.15); position: relative; {special_style}">
                        <span style="font-size: 2rem;">{process['icon']}</span>
                        <div style="position: absolute; top: -10px; right: -10px; background: #1e293b; color: white; width: 25px; height: 25px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: 600;">{process['step']}</div>
                    </div>
                    <h4 style="font-size: 1rem; font-weight: 600; color: #1e293b; margin-bottom: 0.5rem;">{process['title']}</h4>
                    <p style="font-size: 0.85rem; color: #64748b; margin: 0;">{process['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # 화살표 추가 (마지막 단계 제외)
                if i < len(processes_row2) - 1:
                    st.markdown("""
                    <div style="text-align: center; margin: 1rem 0;">
                        <span style="font-size: 1.5rem; color: #cbd5e1;">→</span>
                    </div>
                    """, unsafe_allow_html=True)
        
        # CSS 애니메이션 추가
        st.markdown("""
        <style>
        @keyframes pulse {
            0% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0.7); }
            70% { box-shadow: 0 0 0 10px rgba(255, 107, 107, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 107, 107, 0); }
        }
        </style>
        """, unsafe_allow_html=True)
    
    elif st.session_state.waiting_for_date_input:
        # Step 3.5 완료 후 날짜 입력 대기 화면
        st.markdown("## 📊 특허 동향 그래프 생성 완료!")
        
        # 그래프 표시
        display_patent_graph()
        
        st.markdown("---")
        st.markdown("## 📅 분석 날짜 범위 선택")
        st.write("위 그래프를 참고하여 더 자세히 분석하고 싶은 날짜 범위를 선택하세요.")
        
        st.info("""
        💡 **두 가지 옵션을 제공합니다:**
        - 🚀 **완전한 토픽 분석 실행**: 선택한 날짜 범위의 데이터로 BERTopic 분석 + AI 보고서 생성
        - 📊 **그래프만 먼저 확인**: 토픽 분석 없이 결과 화면으로 이동 (나중에 분석 가능)
        """)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            start_year = st.number_input(
                "시작 연도", 
                min_value=1990, 
                max_value=2025, 
                value=2000,
                step=1
            )
        
        with col2:
            end_year = st.number_input(
                "종료 연도", 
                min_value=1990, 
                max_value=2025, 
                value=2023,
                step=1
            )
        
        with col3:
            st.markdown("<br>", unsafe_allow_html=True)  # 공간 맞추기
            
            # 두 개 버튼을 세로로 배치
            if st.button("🚀 완전한 토픽 분석 실행 (권장)", type="primary", use_container_width=True):
                if start_year <= end_year:
                    with st.spinner("날짜 범위 적용 중..."):
                        filtered_count = filter_data_by_date(start_year, end_year)
                        st.success(f"✅ {start_year}-{end_year} 범위로 필터링 완료! ({filtered_count}건)")
                        
                        # 선택된 날짜 범위를 세션에 저장
                        st.session_state.selected_date_range = {
                            "start_year": start_year,
                            "end_year": end_year,
                            "filtered_count": filtered_count
                        }
                        
                        # Step4부터 재개
                        st.session_state.date_filtered = True
                        continue_analysis_from_step4()
                else:
                    st.error("❌ 시작 연도가 종료 연도보다 클 수 없습니다.")
            
            st.markdown("<br>", unsafe_allow_html=True)  # 버튼 간격
            
            if st.button("📊 그래프만 먼저 확인하기", use_container_width=True):
                if start_year <= end_year:
                    # 날짜 범위 필터링 (데이터 저장 없이 카운트만)
                    try:
                        df = pd.read_csv("./extract_end.csv")
                        df["출원일"] = df["출원일"].astype(str).str.strip()
                        df["출원연도"] = pd.to_datetime(
                            df["출원일"], errors="coerce", infer_datetime_format=True
                        ).dt.year
                        
                        filtered_count = len(df[(df["출원연도"] >= start_year) & (df["출원연도"] <= end_year)])
                        
                        # 선택된 날짜 범위를 세션에 저장
                        st.session_state.selected_date_range = {
                            "start_year": start_year,
                            "end_year": end_year,
                            "filtered_count": filtered_count
                        }
                        
                        # 결과 화면으로 바로 이동 (토픽 분석 결과 없음)
                        st.session_state.analysis_complete = True
                        st.session_state.waiting_for_date_input = False
                        
                        # 토픽 결과를 None으로 설정 (분석 미완료 상태)
                        st.session_state.topic_results = None
                        
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ 데이터 처리 중 오류: {str(e)}")
                else:
                    st.error("❌ 시작 연도가 종료 연도보다 클 수 없습니다.")
        
        # 날짜 범위 미리보기
        if start_year and end_year and start_year <= end_year:
            try:
                df = pd.read_csv("./extract_end.csv")
                df["출원일"] = df["출원일"].astype(str).str.strip()
                df["출원연도"] = pd.to_datetime(
                    df["출원일"], errors="coerce", infer_datetime_format=True
                ).dt.year
                
                total_count = len(df)
                filtered_count = len(df[(df["출원연도"] >= start_year) & (df["출원연도"] <= end_year)])
                
                st.info(f"📊 선택한 날짜 범위의 특허 수: {filtered_count}/{total_count}건 ({filtered_count/total_count*100:.1f}%)")
            except:
                pass

    elif st.session_state.step_progress > 0 and not st.session_state.analysis_complete and not st.session_state.waiting_for_date_input:
        # 분석 진행 중 화면
        st.markdown(f"## 🔄 분석 진행 중... (Step {st.session_state.step_progress}/5)")
        
        # 진행률 표시
        progress_container = st.container()
        with progress_container:
            st.markdown('<div class="progress-container">', unsafe_allow_html=True)
            
            progress_value = st.session_state.step_progress / 5
            st.progress(progress_value)
            
            # 현재 진행 중인 단계 정보
            step_info = {
                1: "🔍 키워드 분석 및 특허식 생성",
                2: "📊 KIPRIS 특허 데이터 크롤링",
                3: "🔧 유사도 기반 데이터 필터링",
                "3_5": "📈 특허 연도별 그래프 생성",
                4: "🤖 BERTopic 토픽 모델링 및 시각화",
                5: "📝 AI 기반 기술 보고서 생성"
            }
            
            for step in [1, 2, 3, "3_5", 4, 5]:
                if step == "3_5":
                    if st.session_state.step_progress > 3:
                        st.success(f"✅ Step 3.5: {step_info[step]} - 완료")
                    elif st.session_state.step_progress == 3:
                        st.info(f"🔄 Step 3.5: {step_info[step]} - 진행 중...")
                    else:
                        st.write(f"⏳ Step 3.5: {step_info[step]} - 대기 중")
                elif isinstance(step, int):
                    if step < st.session_state.step_progress:
                        st.success(f"✅ Step {step}: {step_info[step]} - 완료")
                    elif step == st.session_state.step_progress:
                        st.info(f"🔄 Step {step}: {step_info[step]} - 진행 중...")
                    else:
                        st.write(f"⏳ Step {step}: {step_info[step]} - 대기 중")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.analysis_complete:
        # 분석 완료 화면
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("## 🎉 분석 완료!")
        
        with col2:
            # 선택된 날짜 범위 표시 (세련된 뱃지 스타일)
            if hasattr(st.session_state, 'selected_date_range') and st.session_state.selected_date_range:
                date_info = st.session_state.selected_date_range
                st.markdown(f"""
                <div style="text-align: right; margin-top: 0.5rem;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 0.5rem 1rem; border-radius: 20px; display: inline-block; font-size: 0.9rem; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);">
                        📅 {date_info['start_year']}-{date_info['end_year']} 기간 • {date_info['filtered_count']}건 분석
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        # 완료 메시지
        if hasattr(st.session_state, 'selected_date_range') and st.session_state.selected_date_range:
            date_info = st.session_state.selected_date_range
            period_text = f"{date_info['start_year']}-{date_info['end_year']}"
            st.info(f"🎯 **{period_text}** 기간으로 맞춤 분석이 완료되었습니다! 선택하신 **{date_info['filtered_count']}건**의 특허 데이터를 바탕으로 정밀한 인사이트를 제공합니다.")
        
        # 탭으로 결과 구분 - 특허 그래프 탭 추가
        tab1, tab2, tab3, tab4 = st.tabs(["📈 특허 동향 그래프", "📊 토픽 분석 결과", "🖼️ 시각화", "📋 기술 보고서"])
        
        with tab1:
            display_patent_graph()
        
        with tab2:
            display_topic_results()
        
        with tab3:
            display_topic_visualization()
        
        with tab4:
            display_generated_reports()

if __name__ == "__main__":
    main()