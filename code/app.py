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
    step4_module = importlib.import_module('step4_벌토픽')
    step5_module = importlib.import_module('step5_보고서작성')
    
    Step1 = step1_module.Step1
    Step2 = step2_module.Step2
    Step3 = step3_module.Step3
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
        background-color: #f8f9fa;
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
        background-color: #f0f8ff;
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

def update_progress(step, message):
    """진행 상황 업데이트"""
    progress_data = {
        "stage": f"Step {step}",
        "current": step,
        "total": 5,
        "message": message
    }
    with open("progress.json", "w", encoding="utf-8") as f:
        json.dump(progress_data, f, ensure_ascii=False)
    
    st.session_state.step_progress = step

def run_analysis_pipeline(keyword):
    """main.py의 generate_report 함수와 동일한 분석 파이프라인"""
    
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    try:
        # Step 1: 특허식 생성
        with status_placeholder.container():
            st.info("🔍 Step 1: 키워드 분석 및 특허식 생성 중...")
        update_progress(1, f"키워드 '{keyword}'로 특허식 생성 중...")
        
        s1 = Step1()
        sentence = s1.make(keyword)
        
        with status_placeholder.container():
            st.success("✅ Step 1 완료: 특허식 생성 완료")
        
        # Step 2: 특허 크롤링
        with status_placeholder.container():
            st.info("📊 Step 2: KIPRIS 특허 데이터 크롤링 중...")
        update_progress(2, "특허 크롤링 중...")
        
        s2 = Step2()
        s2.cra(sentence)
        
        with status_placeholder.container():
            st.success("✅ Step 2 완료: 특허 데이터 수집 완료")
        
        # Step 3: 데이터 필터링
        with status_placeholder.container():
            st.info("🔧 Step 3: 유사도 기반 특허 필터링 중...")
        update_progress(3, "특허 필터링 중...")
        
        s3 = Step3()
        s3.filter()
        
        with status_placeholder.container():
            st.success("✅ Step 3 완료: 데이터 필터링 완료")
        
        # Step 4: 토픽 모델링
        with status_placeholder.container():
            st.info("🤖 Step 4: BERTopic 토픽 모델링 및 시각화 중...")
        update_progress(4, "토픽 추출 및 시각화 중...")
        
        s4 = Step4()
        topic_list = s4.ber()
        
        with status_placeholder.container():
            st.success("✅ Step 4 완료: 토픽 추출 및 시각화 완료")
        
        # Step 5: 보고서 생성
        with status_placeholder.container():
            st.info("📝 Step 5: AI 기반 기술 보고서 작성 중...")
        update_progress(5, "보고서 작성 중...")
        
        s5 = Step5()
        report = s5.last(topic_list)
        
        with status_placeholder.container():
            st.success("🎉 Step 5 완료: 기술 보고서 생성 완료!")
        
        # 결과 저장
        st.session_state.topic_results = topic_list
        st.session_state.analysis_complete = True
        
        return topic_list
        
    except Exception as e:
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
    topic_words_image_path = "topic_words_chart.png"
    if os.path.exists(topic_words_image_path):
        image2 = Image.open(topic_words_image_path)
        st.image(image2, caption="토픽별 상위 12개 주요 키워드 분포", use_column_width=True)
    else:
        st.info("토픽 키워드 차트 이미지를 찾을 수 없습니다.")

def display_generated_reports():
    """생성된 보고서 목록 및 내용 표시"""
    st.subheader("📋 생성된 기술 보고서")
    
    reports_dir = "generated_reports"
    if not os.path.exists(reports_dir):
        st.warning("생성된 보고서가 없습니다.")
        return
    
    report_files = glob.glob(os.path.join(reports_dir, "*.md"))
    
    if not report_files:
        st.warning("생성된 보고서가 없습니다.")
        return
    
    # 보고서 선택
    report_names = [os.path.basename(f) for f in report_files]
    selected_report = st.selectbox("보고서 선택:", report_names)
    
    if selected_report:
        report_path = os.path.join(reports_dir, selected_report)
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 중복된 # 제목 제거 (첫 번째 # 제목만 유지)
            lines = content.split('\n')
            cleaned_lines = []
            first_h1_found = False
            
            for line in lines:
                if line.strip().startswith('# ') and not first_h1_found:
                    # 첫 번째 # 제목은 유지
                    cleaned_lines.append(line)
                    first_h1_found = True
                elif line.strip().startswith('# ') and first_h1_found:
                    # 두 번째 이후 # 제목은 ## 로 변경하거나 제거
                    continue  # 완전히 제거
                else:
                    cleaned_lines.append(line)
            
            cleaned_content = '\n'.join(cleaned_lines)
            st.markdown(cleaned_content)
        except Exception as e:
            st.error(f"보고서를 읽는 중 오류 발생: {str(e)}")

def display_topic_results():
    """토픽 분석 결과 표시"""
    if st.session_state.topic_results:
        st.subheader("🔍 토픽 분석 결과")
        
        for topic_id, words in st.session_state.topic_results.items():
            with st.expander(f"Topic {topic_id + 1}"):
                st.write("**주요 키워드:**")
                st.write(", ".join(words[:10]))  # 상위 10개 키워드만 표시

def main():
    # 상단 배경 이미지를 맨 위에 붙히기 위한 CSS
    st.markdown("""
    <style>
    .main > div {
        padding-top: 0rem !important;
        padding-left: 0rem !important;
        padding-right: 0rem !important;
        max-width: 100% !important;
    }
    .stApp > header {
        background-color: transparent;
        height: 0px;
    }
    .stApp {
        padding-top: 0rem !important;
    }
    .top-banner {
        width: 95vw;
        height: 350px;
        margin: 0 auto;
        padding: 0;
        display: block;
        margin-top: -2rem;
        position: relative;
        z-index: 999;
    }
    .top-banner img {
        width: 100%;
        height: 350px;
        object-fit: contain;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 상단 배경 이미지
    possible_paths = ["./top2.png", "top2.png", "../top2.png", "code/top2.png"]
    
    for path in possible_paths:
        if os.path.exists(path):
            top_image = Image.open(path)
            
            # HTML로 이미지 직접 삽입
            import base64
            from io import BytesIO
            
            # 이미지를 base64로 인코딩
            buffer = BytesIO()
            top_image.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            st.markdown(f"""
            <div class="top-banner">
                <img src="data:image/png;base64,{img_str}" alt="Top Banner">
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
            placeholder="예: 자율주행 로봇, 인공지능, 블록체인"
        )
        
        # 분석 시작 버튼
        if st.button("🚀 분석 시작", type="primary", disabled=not keyword):
            st.session_state.keyword_input = keyword
            st.session_state.analysis_complete = False
            st.session_state.topic_results = None
            st.session_state.step_progress = 0
            
            # 분석 실행
            with st.spinner("분석을 진행 중입니다..."):
                run_analysis_pipeline(keyword)
        
        # 진행 상황 표시
        if st.session_state.step_progress > 0:
            st.markdown("### 📈 진행 상황")
            progress_value = st.session_state.step_progress / 5
            st.progress(progress_value)
            st.write(f"Step {st.session_state.step_progress}/5 완료")
        
        # 분석 완료 후 옵션
        if st.session_state.analysis_complete:
            st.success("✅ 분석 완료!")
            if st.button("🔄 새로운 분석"):
                st.session_state.analysis_complete = False
                st.session_state.topic_results = None
                st.session_state.step_progress = 0
                st.session_state.keyword_input = ""
                st.rerun()
    
    # 메인 컨텐츠 영역
    if not st.session_state.analysis_complete and st.session_state.step_progress == 0:
        # 초기 화면
        st.markdown("""
        ## 🎯 시스템 소개
        
        이 시스템은 AI를 활용하여 특허 데이터를 분석하고 기술 보고서를 자동 생성합니다.
        
        ### 📋 주요 기능
        
        1. **🔍 특허식 생성**: 입력 키워드를 바탕으로 KIPRIS 검색식 자동 생성
        2. **📊 특허 크롤링**: KIPRIS API를 통한 관련 특허 데이터 수집
        3. **🔧 데이터 필터링**: AI 임베딩을 활용한 유사도 기반 필터링
        4. **🤖 토픽 모델링**: BERTopic을 이용한 토픽 추출 및 시각화
        5. **📝 보고서 생성**: LLM을 활용한 기술 보고서 자동 작성
        
        ### 🚀 시작하기
        
        왼쪽 사이드바에서 분석하고 싶은 기술 키워드를 입력하고 '분석 시작' 버튼을 클릭하세요.
        """)
        
        # 시스템 아키텍처 다이어그램
        st.markdown("### 🏗️ 시스템 구조")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown("""
            <div class="step-container">
                <div class="step-title">Step 1</div>
                <p>특허식 생성</p>
                <p>🔍 GPT-3.5</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="step-container">
                <div class="step-title">Step 2</div>
                <p>특허 크롤링</p>
                <p>📊 KIPRIS API</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="step-container">
                <div class="step-title">Step 3</div>
                <p>데이터 필터링</p>
                <p>🔧 OpenAI Embedding</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="step-container">
                <div class="step-title">Step 4</div>
                <p>토픽 모델링</p>
                <p>🤖 BERTopic</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            st.markdown("""
            <div class="step-container">
                <div class="step-title">Step 5</div>
                <p>보고서 생성</p>
                <p>📝 GPT-4</p>
            </div>
            """, unsafe_allow_html=True)
    
    elif st.session_state.step_progress > 0 and not st.session_state.analysis_complete:
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
                4: "🤖 BERTopic 토픽 모델링 및 시각화",
                5: "📝 AI 기반 기술 보고서 생성"
            }
            
            for step in range(1, 6):
                if step < st.session_state.step_progress:
                    st.success(f"✅ Step {step}: {step_info[step]} - 완료")
                elif step == st.session_state.step_progress:
                    st.info(f"🔄 Step {step}: {step_info[step]} - 진행 중...")
                else:
                    st.write(f"⏳ Step {step}: {step_info[step]} - 대기 중")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    elif st.session_state.analysis_complete:
        # 분석 완료 화면
        st.markdown("## 🎉 분석 완료!")
        
        # 탭으로 결과 구분
        tab1, tab2, tab3 = st.tabs(["📊 토픽 분석 결과", "🖼️ 시각화", "📋 기술 보고서"])
        
        with tab1:
            display_topic_results()
        
        with tab2:
            display_topic_visualization()
        
        with tab3:
            display_generated_reports()

if __name__ == "__main__":
    main()