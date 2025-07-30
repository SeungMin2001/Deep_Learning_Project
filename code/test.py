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
    topic_words_image_path = "./topic_words_chart.png"
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
            st.markdown(content)
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
    /* 사이드바 폭 조정 */
    .css-1d391kg {
        width: 320px !important;
    }
    section[data-testid="stSidebar"] {
        width: 320px !important;
    }
    .css-1cypcdb {
        width: 320px !important;
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
        # 첫 화면 - 히어로 섹션
        st.markdown("""
        <div style="text-align: center; margin: 2rem 0 3rem 0;">
            <h1 style="font-size: 3rem; font-weight: 700; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 1rem;">
                🎆 AI 특허 분석 플랫폼
            </h1>
            <h2 style="font-size: 1.8rem; font-weight: 400; color: #64748b; margin-bottom: 1.5rem;">
                지능형 기술 보고서 자동 생성
            </h2>
            <p style="font-size: 1.1rem; color: #64748b; line-height: 1.6; max-width: 600px; margin: 0 auto;">
                최첨단 AI 기술로 특허 데이터를 분석하고<br>전문적인 인사이트가 담긴 기술 보고서를 자동 생성합니다
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # 3개 열로 나눠서 기능 소개
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center;">
                <h3>⚡ 신속한 분석</h3>
                <p>AI 기반 자동화로 5분 안에 완료</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center;">
                <h3>🎯 정확한 인사이트</h3>
                <p>최신 NLP 기술로 핵심 토픽 추출</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center;">
                <h3>📈 전문 보고서</h3>
                <p>GPT-4 기반 고품질 기술 보고서 생성</p>
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
            <p style="text-align: center; font-size: 1.1rem; color: #64748b; margin-bottom: 4rem; max-width: 600px; margin-left: auto; margin-right: auto;">
                5단계 AI 분석 프로세스를 통해 전문적인 특허 분석 보고서를 자동으로 생성합니다
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
            <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 2rem; border-radius: 20px; color: white; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(79, 172, 254, 0.3);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📝</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: white;">자동 보고서 생성</h3>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5; color: white;">GPT-4를 활용하여 분석 결과를 바탕으로 전문적인 기술 보고서를 자동 작성합니다.</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 2rem; border-radius: 20px; color: white; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(250, 112, 154, 0.3);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📊</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: white;">대용량 특허 크롤링</h3>
                <p style="font-size: 1rem; opacity: 0.9; line-height: 1.5; color: white;">KIPRIS API를 통해 관련 특허 데이터를 체계적으로 수집하고 구조화합니다.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 2rem; border-radius: 20px; color: #333; margin-bottom: 1.5rem; box-shadow: 0 10px 25px rgba(168, 237, 234, 0.3);">
                <div style="font-size: 3rem; margin-bottom: 1rem;">🤖</div>
                <h3 style="font-size: 1.4rem; font-weight: 600; margin-bottom: 0.8rem; color: #333;">BERTopic 토픽 모델링</h3>
                <p style="font-size: 1rem; opacity: 0.8; line-height: 1.5; color: #333;">최신 NLP 기술로 특허 문서에서 핵심 토픽을 추출하고 직관적으로 시각화합니다.</p>
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
            <h2 style="text-align: center; font-size: 2.2rem; font-weight: 600; color: #1e293b; margin-bottom: 3rem;">⚡ 분석 프로세스</h2>
        </div>
        """, unsafe_allow_html=True)
        
        # 5단계 프로세스를 가로로 배치
        col1, col2, col3, col4, col5 = st.columns(5, gap="medium")
        
        processes = [
            {"step": "01", "title": "특허식 생성", "desc": "AI 키워드 분석", "icon": "🔍", "color": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"},
            {"step": "02", "title": "데이터 크롤링", "desc": "KIPRIS API 연동", "icon": "📊", "color": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)"},
            {"step": "03", "title": "스마트 필터링", "desc": "AI 임베딩 분석", "icon": "🔧", "color": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)"},
            {"step": "04", "title": "토픽 모델링", "desc": "BERTopic 분석", "icon": "🤖", "color": "linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)"},
            {"step": "05", "title": "보고서 생성", "desc": "GPT-4 작성", "icon": "📝", "color": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"}
        ]
        
        columns = [col1, col2, col3, col4, col5]
        
        for i, (col, process) in enumerate(zip(columns, processes)):
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
                if i < len(processes) - 1:
                    st.markdown("""
                    <div style="text-align: center; margin: 1rem 0;">
                        <span style="font-size: 1.5rem; color: #cbd5e1;">→</span>
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