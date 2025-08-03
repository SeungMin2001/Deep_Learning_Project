import streamlit as st
import json
import glob
import os
from datetime import datetime
import plotly.graph_objects as go
from PIL import Image
import pandas as pd
import time
import sys
import importlib
from wordcloud import WordCloud
import matplotlib.pyplot as plt

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
    page_icon="icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일
st.markdown("""
<style>
    /* 사이드바 로고 스타일 개선 */
    section[data-testid="stSidebar"] .element-container:first-child {
        margin-top: -1rem;
    }
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
if "current_page" not in st.session_state:
    st.session_state.current_page = "home"
if "selected_topic" not in st.session_state:
    st.session_state.selected_topic = None

def show_sidebar_logo():
    """사이드바 상단에 세련된 그라데이션 로고 표시"""
    import base64
    
    # icon.png 파일을 base64로 인코딩
    try:
        with open("./code/icon.png", "rb") as f:
            icon_data = base64.b64encode(f.read()).decode()
        icon_base64 = f"data:image/png;base64,{icon_data}"
        
        st.markdown(f"""
        <style>
        .premium-logo-container {{
            position: relative;
            background: 
                linear-gradient(145deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 50%, transparent 100%),
                linear-gradient(to bottom right, 
                    rgba(0, 122, 255, 0.08) 0%,
                    rgba(88, 86, 214, 0.06) 25%,
                    rgba(255, 45, 85, 0.04) 50%,
                    rgba(255, 149, 0, 0.06) 75%,
                    rgba(52, 199, 89, 0.05) 100%);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-radius: 22px;
            box-shadow: 
                0 20px 40px -12px rgba(0, 0, 0, 0.12),
                0 8px 16px -8px rgba(0, 0, 0, 0.08),
                inset 0 1px 0 rgba(255, 255, 255, 0.35),
                inset 0 -1px 0 rgba(0, 0, 0, 0.03);
            backdrop-filter: blur(20px) saturate(150%);
            -webkit-backdrop-filter: blur(20px) saturate(150%);
            overflow: hidden;
        }}
        
        .premium-logo-container::before {{
            content: '';
            position: absolute;
            top: -2px;
            left: -2px;
            right: -2px;
            bottom: -2px;
            background: linear-gradient(45deg, 
                rgba(0, 122, 255, 0.3) 0%,
                rgba(88, 86, 214, 0.25) 20%,
                rgba(255, 45, 85, 0.25) 40%,
                rgba(255, 149, 0, 0.3) 60%,
                rgba(52, 199, 89, 0.25) 80%,
                rgba(0, 122, 255, 0.3) 100%);
            border-radius: 24px;
            z-index: -1;
            opacity: 0;
            transition: opacity 0.4s ease;
        }}
        
        .premium-logo-container::after {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 30% 20%, 
                rgba(255, 255, 255, 0.15) 0%,
                transparent 60%);
            border-radius: inherit;
            z-index: 1;
        }}
        
        .logo-icon {{
            position: relative;
            z-index: 3;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            filter: drop-shadow(0 8px 24px rgba(0, 0, 0, 0.12))
                   drop-shadow(0 4px 8px rgba(0, 0, 0, 0.08));
        }}
        
        .premium-logo-container:hover {{
            transform: translateY(-4px) scale(1.02);
            box-shadow: 
                0 32px 64px -16px rgba(0, 0, 0, 0.18),
                0 16px 32px -12px rgba(0, 0, 0, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.4),
                inset 0 -1px 0 rgba(0, 0, 0, 0.06);
        }}
        
        .premium-logo-container:hover::before {{
            opacity: 1;
        }}
        
        .premium-logo-container:hover .logo-icon {{
            transform: scale(1.05) rotateY(5deg);
            filter: drop-shadow(0 12px 32px rgba(0, 0, 0, 0.15))
                   drop-shadow(0 6px 16px rgba(0, 0, 0, 0.1))
                   brightness(1.08)
                   contrast(1.02);
        }}
        
        .premium-logo-container:active {{
            transform: translateY(-2px) scale(1.01);
            transition: all 0.1s ease;
        }}
        
        /* Subtle animation */
        @keyframes logoBreath {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.01); }}
        }}
        
        .premium-logo-container {{
            animation: logoBreath 4s ease-in-out infinite;
        }}
        </style>
        
        <div style="
            display: flex;
            align-items: center;
            justify-content: center;
            margin: -3rem 0 5rem 0;
            padding: 1.0rem 1.0rem;
            cursor: pointer;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        " class="premium-logo-container" onclick="window.location.reload();">
            <img src="{icon_base64}" alt="AI Patent Intelligence System" class="logo-icon" style="
                width: 130px;
                height: 90px;
                object-fit: contain;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            "/>
        </div>
        """, unsafe_allow_html=True)
        
    except FileNotFoundError:
        # icon.png 파일이 없으면 기본 로고 표시
        st.markdown("""
        <div style="
            text-align: center;
            padding: 2rem 1.5rem;
            background: 
                linear-gradient(145deg, rgba(255, 255, 255, 0.1) 0%, transparent 50%),
                linear-gradient(to bottom right, 
                    rgba(79, 172, 254, 0.12) 0%,
                    rgba(0, 242, 254, 0.08) 35%,
                    rgba(147, 51, 234, 0.06) 65%,
                    rgba(79, 172, 254, 0.1) 100%);
            border: 1px solid rgba(255, 255, 255, 0.18);
            border-radius: 24px;
            box-shadow: 
                0 20px 40px -12px rgba(79, 172, 254, 0.15),
                0 8px 16px -8px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(16px) saturate(120%);
            margin: 1.5rem 0 2.5rem 0;
            cursor: pointer;
            transition: all 0.3s ease;
        " onclick="window.location.reload();">
            <div style="
                font-size: 3.5rem; 
                margin-bottom: 0.8rem; 
                filter: drop-shadow(0 4px 8px rgba(79, 172, 254, 0.2));
            ">🔬</div>
            <div style="
                font-size: 1rem; 
                font-weight: 700; 
                background: linear-gradient(135deg, #007AFF 0%, #5856D6 50%, #FF2D55 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                line-height: 1.2;
            ">AI Patent Intelligence</div>
        </div>
        """, unsafe_allow_html=True)

def show_sidebar_footer():
    """사이드바 하단에 홈으로 가기 버튼"""
    # 하단 고정 버튼
    st.markdown("""
    <div style="
        position: fixed;
        bottom: 2rem;
        left: 1rem;
        right: 1rem;
        width: calc(320px - 2rem);
        z-index: 999;
    ">
    """, unsafe_allow_html=True)
    
    if st.button("🏠 홈으로 가기", key="sidebar_home_button", help="홈 화면으로 이동", use_container_width=True):
        # 세션 상태 완전 초기화 (완전히 처음 상태로 돌아가기)
        st.session_state.current_page = "home"
        st.session_state.analysis_complete = False
        st.session_state.step_progress = 0
        st.session_state.topic_results = None
        st.session_state.waiting_for_date_input = False
        st.session_state.keyword_input = ""
        if hasattr(st.session_state, 'date_filtered'):
            st.session_state.date_filtered = False
        if hasattr(st.session_state, 'selected_date_range'):
            del st.session_state.selected_date_range
        if hasattr(st.session_state, 'generated_keywords'):
            del st.session_state.generated_keywords
        if hasattr(st.session_state, 'graph_data'):
            del st.session_state.graph_data
        st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 하단 버튼 스타일링
    st.markdown("""
    <style>
    /* 하단 홈 버튼 스타일링 */
    [data-testid*="sidebar_home_button"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 25px !important;
        font-size: 0.9rem !important;
        padding: 0.8rem 1.5rem !important;
        font-weight: 600 !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid*="sidebar_home_button"]:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    </style>
    """, unsafe_allow_html=True)

def show_navigation():
    """추가 네비게이션 (필요시 사용)"""
    # 로고가 사이드바로 이동했으므로 메인 네비게이션은 불필요
    pass

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
        
        # openDate가 있는 데이터만 필터링
        df = df.dropna(subset=['openDate'])
        
        # openDate 처리 (step3_5_특허그래프.py와 동일한 방식)
        df["openDate"] = df["openDate"].astype(str).str.replace('.0', '').str.strip()
        df["출원연도"] = pd.to_datetime(
            df["openDate"], format='%Y%m%d', errors="coerce"
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
    
        def simple_progress_update(step_num, step_name, icon):
            """단순 진행률 업데이트 (스레드 없음)"""
            nonlocal base_progress
            status_container.info(f"{icon} Step {step_num}: {step_name} 중...")
            current_progress = base_progress + (step_weights[step_num] * 0.5)  # 중간 진행률
            main_progress.progress(current_progress)
    
    try:
        
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
        #detail_container.write(f"✅ 생성된 특허식: {sentence}")
        time.sleep(5.0)  # 5초 동안 완료 메시지 유지
        
        # Step 2: 특허 크롤링
        update_progress(2, "특허 크롤링 중...")
        
        # 동기식 진행률 업데이트
        simple_progress_update(2, "KIPRIS 특허 데이터 크롤링", "📊")
        
        s2 = Step2()
        s2.cra(sentence)
        
        base_progress += step_weights[2]
        main_progress.progress(base_progress)
        status_container.success("✅ Step 2 완료: 특허 데이터 수집 완료")
        time.sleep(5.0)  # 5초 동안 완료 메시지 유지
        
        # Step 3: 데이터 필터링
        update_progress(3, "특허 필터링 중...")
        
        simple_progress_update(3, "유사도 기반 특허 필터링", "🔧")
        
        s3 = Step3()
        s3.filter()
        
        base_progress += step_weights[3]
        main_progress.progress(base_progress)
        status_container.success("✅ Step 3 완료: 데이터 필터링 완료")
        time.sleep(5.0)  # 5초 동안 완료 메시지 유지
        
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
        status_container.success("🎯 Step 3.5 완료: 특허 그래프 생성 완료")
        detail_container.write("📈 연도별 특허 출원 동향 그래프가 생성되었습니다.")
        
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
        
    # Step 4: 토픽 모델링 (스레드 없이 동기식 처리)
    def update_progress(step, message):
        """진행률 업데이트 헬퍼 함수"""
        current_progress = sum(step_weights[k] for k in step_weights.keys() if (isinstance(k, int) and k < step) or (isinstance(k, str) and k == "3_5" and step > 3))
        main_progress.progress(current_progress)
    
    update_progress(4, "토픽 추출 및 시각화 중...")
    status_container.info("🤖 Step 4: BERTopic 토픽 모델링 및 시각화 중...")
    
    try:
        
        s4 = Step4()
        topic_list = s4.ber()
        
        # 토픽 결과 검증 및 로깅
        print(f"🔍 Step4에서 받은 토픽 결과: {type(topic_list)}")
        if isinstance(topic_list, dict):
            print(f"📊 토픽 개수: {len(topic_list)}개")
            for topic_id, words in topic_list.items():
                print(f"  - Topic {topic_id}: {words[:3]}...")
        
        if not topic_list or not isinstance(topic_list, dict):
            main_progress.progress(0.9)
            status_container.error("❌ Step 4 실패: 토픽 추출 중 오류 발생")
            detail_container.error("토픽 모델링에 실패했습니다. 데이터를 확인해주세요.")
            return None
            
        base_progress += step_weights[4]
        main_progress.progress(base_progress)
        status_container.success("✅ Step 4 완료: 토픽 추출 및 시각화 완료")
        detail_container.write(f"✅ {len(topic_list)}개의 주요 토픽을 발견했습니다.")
        time.sleep(5.0)  # 5초 동안 완료 메시지 유지
        
        # Step 5: 보고서 생성
        update_progress(5, "보고서 작성 중...")
        
        status_container.info("📝 Step 5: AI 기반 기술 보고서 작성 중...")
        
        s5 = Step5()
        s5.last(topic_list)
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
    
    # UMAP 이미지 표시 (캐시 방지)
    st.markdown("### 🗺️ UMAP 2D 토픽 분포")
    umap_image_path = "umap2d_topics_custom_color_pret.png"
    if os.path.exists(umap_image_path):
        # 파일 수정 시간을 체크하여 캐시 강제 갱신
        import time
        file_mtime = os.path.getmtime(umap_image_path)
        cache_key = f"umap_image_{file_mtime}"
        
        # 캐시를 무시하고 이미지 다시 로드
        with open(umap_image_path, 'rb') as f:
            image_bytes = f.read()
        image = Image.open(umap_image_path)
        st.image(image, caption="UMAP 2D 토픽 분포도", use_container_width=True)
    else:
        st.warning("UMAP 시각화 이미지를 찾을 수 없습니다.")
    
    # Topic Words Chart 이미지 표시 (캐시 방지)
    st.markdown("### 📈 토픽별 주요 키워드")
    topic_words_image_path = "./topic_words_chart.png"
    if os.path.exists(topic_words_image_path):
        # 파일 수정 시간을 체크하여 캐시 강제 갱신
        file_mtime2 = os.path.getmtime(topic_words_image_path)
        cache_key2 = f"topic_chart_{file_mtime2}"
        
        # 캐시를 무시하고 이미지 다시 로드
        with open(topic_words_image_path, 'rb') as f:
            image_bytes2 = f.read()
        image2 = Image.open(topic_words_image_path)
        st.image(image2, caption="토픽별 주요 키워드 차트", use_container_width=True)
    else:
        st.info("토픽 키워드 차트 이미지를 찾을 수 없습니다.")
    
    # 워드클라우드 표시
    st.markdown("### ☁️ 워드 클라우드")
    display_word_cloud()


def display_word_cloud():
    """주요 토픽의 상위 키워드로 워드클라우드 생성 및 표시"""
    try:
        # BERTopic 결과에서 토픽 키워드 추출
        topic_keywords = {}
        word_frequencies = {}
        
        # generated_reports 폴더에서 토픽 보고서 파일들 찾기
        report_files = glob.glob("generated_reports/Topic_*.md.md")
        
        if report_files:
            for report_file in report_files:
                try:
                    with open(report_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # 핵심 키워드 라인 찾기 (예: **핵심 키워드:** 센서, 카메라, 지능, 인공, 빅데이터, 알고리즘, 서버, 저장, 학습, 온도)
                    lines = content.split('\n')
                    
                    for line in lines:
                        if '핵심 키워드:' in line or '**핵심 키워드:**' in line:
                            # 키워드 추출
                            keyword_part = line.split('핵심 키워드:')[-1].strip()
                            # ** 제거
                            keyword_part = keyword_part.replace('**', '').strip()
                            if keyword_part:
                                # 쉼표로 분리된 키워드들 추출
                                keywords = [kw.strip().replace('**', '') for kw in keyword_part.split(',')]
                                for i, keyword in enumerate(keywords):
                                    # 빈 문자열이나 특수문자만 있는 키워드 제외
                                    keyword = keyword.strip()
                                    if keyword and len(keyword) > 1 and not keyword.startswith('*'):
                                        # 첫 번째 키워드가 가장 중요하다고 가정하고 가중치 부여
                                        weight = 1.0 - (i * 0.05)  # 순서대로 가중치 감소
                                        word_frequencies[keyword] = max(weight, 0.1)
                            break
                except Exception as e:
                    continue
        
        # 세션 상태에서 토픽 정보 가져오기 (대안)
        if not word_frequencies and hasattr(st.session_state, 'topic_results'):
            try:
                topics_info = st.session_state.topic_results
                for topic_info in topics_info:
                    if 'keywords' in topic_info:
                        for keyword, weight in topic_info['keywords']:
                            word_frequencies[keyword] = float(weight)
            except:
                pass
        
        if word_frequencies:
            # 워드클라우드 생성
            font_path = './data/Pretendard-1.3.9/public/variable/PretendardVariable.ttf'
            wordcloud = WordCloud(
                width=800, 
                height=400,
                background_color='white',
                font_path=font_path if os.path.exists(font_path) else None,
                max_words=50,
                relative_scaling=0.5,
                colormap='viridis',
                prefer_horizontal=0.7
            ).generate_from_frequencies(word_frequencies)
            
            # matplotlib로 이미지 생성
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            
            # Streamlit에 표시
            st.pyplot(plt, use_container_width=True)
            st.caption("📝 주요 토픽들의 상위 키워드 워드클라우드")
        else:
            st.warning("토픽 키워드 데이터를 찾을 수 없습니다. 토픽 분석을 먼저 완료해주세요.")
            
    except Exception as e:
        st.error(f"워드클라우드 생성 중 오류 발생: {str(e)}")


def display_patent_graph():
    """특허 연도별 그래프 표시 (step3_5 내용)"""
    st.subheader("📊 연도별 특허 출원 동향")
    st.write("모든 키워드에 해당하는 특허의 연도별 출원 건수를 통합하여 표시합니다.")
    
    # 세션 상태에서 그래프 데이터 가져오기
    if hasattr(st.session_state, 'graph_data') and st.session_state.graph_data is not None:
        final_df = st.session_state.graph_data
        
        # 사용자 입력 키워드 기반 그래프 설명 (삭제됨)
        
        # 📊 조건부 색상 막대 차트 출력 (이전년도 대비 증감에 따라 색상 변경)
        
        # 이전년도 대비 증감 계산
        final_df_reset = final_df.reset_index()
        final_df_reset['이전년도_건수'] = final_df_reset['전체 특허 출원 건수'].shift(1)
        final_df_reset['증감'] = final_df_reset['전체 특허 출원 건수'] - final_df_reset['이전년도_건수']
        
        # 색상 조건 설정 (증가=빨간색, 감소=파란색, 동일=회색)
        colors = []
        for idx, row in final_df_reset.iterrows():
            if pd.isna(row['증감']) or row['증감'] == 0:
                colors.append('#808080')  # 회색 (첫해 또는 동일)
            elif row['증감'] > 0:
                colors.append('#FF4444')  # 빨간색 (증가)
            else:
                colors.append('#4444FF')  # 파란색 (감소)
        
        # Plotly 막대 차트 생성
        fig = go.Figure(data=[
            go.Bar(
                x=final_df_reset['출원연도'],
                y=final_df_reset['전체 특허 출원 건수'],
                marker_color=colors,
                hovertemplate='<b>%{x}년</b><br>특허 출원 건수: %{y}건<extra></extra>'
            )
        ])
        
        fig.update_layout(
            title="연도별 특허 출원 동향 (빨간색: 증가, 파란색: 감소)",
            xaxis_title="연도",
            yaxis_title="특허 출원 건수",
            showlegend=False,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        # 그래프 데이터가 없으면 Step3_5 클래스로 새로 생성
        try:
            s3_5 = Step3_5()
            keywords = st.session_state.generated_keywords if hasattr(st.session_state, 'generated_keywords') else None
            final_df = s3_5.generate_graph(keywords)
            
            if final_df is not None:
                st.line_chart(final_df, use_container_width=True, color=["#667eea"])
            else:
                st.error("❌ 그래프 데이터를 생성할 수 없습니다.")
        except Exception as e:
            st.error(f"그래프 생성 중 오류 발생: {str(e)}")

def get_report_files():
    """보고서 파일 목록을 가져오는 공통 함수"""
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
        return None, []
    report_files = sorted(glob.glob(os.path.join(found_reports_dir, "*.md")))
    #report_files = sorted(os.listdir(found_reports_dir))
    return found_reports_dir, report_files

def display_sidebar_reports():
    """사이드바에서 보고서 선택"""
    found_reports_dir, report_files = get_report_files()
    
    if not found_reports_dir or not report_files:
        st.info("📋 보고서 없음")
        return None, None
    
    # 이미 get_report_files()에서 최신순으로 정렬됨
    
    st.subheader("📚 분석 보고서")
    st.caption(f"총 {len(report_files)}개")
    
    # 보고서 선택
    report_names = [os.path.basename(f) for f in report_files]
    report_display_names = []
    
    for i, report_file in enumerate(report_files):
        file_time = datetime.fromtimestamp(os.path.getmtime(report_file))
        report_name = os.path.basename(report_file)
        # 파일명을 더 간결하게 표시
        display_name = report_name.replace('.md', '').replace('Topic_', 'T')
        report_display_names.append(f"{display_name}")
    
    selected_index = st.selectbox(
        "보고서 선택:",
        range(len(report_files)),
        format_func=lambda i: report_display_names[i],
        index=0 if report_files else None,
        key="sidebar_report_select"
    )
    
    if selected_index is not None:
        selected_file = report_files[selected_index]
        selected_name = report_names[selected_index]
        return selected_file, selected_name
    
    return None, None

def display_selected_report():
    """선택된 보고서를 메인 화면에 표시"""
    # 세션 상태에서 선택된 보고서 정보 가져오기
    if "sidebar_report_select" in st.session_state:
        found_reports_dir, report_files = get_report_files()
        
        if found_reports_dir and report_files:
            # 이미 get_report_files()에서 최신순으로 정렬됨
            
            selected_index = st.session_state.sidebar_report_select
            if selected_index < len(report_files):
                selected_file = report_files[selected_index]
                selected_name = os.path.basename(selected_file)
                
                try:
                    with open(selected_file, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    st.markdown("---")
                    
                    # 보고서 제목만 표시 (메인 화면 보고서 탭에서는 다운로드 버튼 없음)
                    st.markdown(f"## 📋 {selected_name}")
                    
                    st.markdown(content)
                    return
                    
                except Exception as e:
                    st.error(f"보고서를 읽는 중 오류 발생: {str(e)}")
                    return
    
    # 선택된 보고서가 없거나 오류가 있는 경우
    st.info("📋 아직 생성된 보고서가 없습니다.")
    st.caption("분석을 완료하면 여기에 보고서가 표시됩니다.")

def display_single_docx_download_for_analysis(report_name):
    """분석 결과 페이지에서 선택된 보고서에 해당하는 DOCX 다운로드 버튼만 표시"""
    found_docx_dir, docx_files = get_recent_docx_files()
    
    if not found_docx_dir or not docx_files:
        return
    
    # 최근 10분 이내에 생성된 DOCX 파일만 필터링 (방금 완료한 분석만)
    from datetime import datetime
    current_time = datetime.now()
    recent_docx = []
    
    for docx_file in docx_files:
        file_time = datetime.fromtimestamp(os.path.getmtime(docx_file))
        time_diff = (current_time - file_time).total_seconds() / 60  # 분 단위
        if time_diff <= 10:  # 10분 이내만
            recent_docx.append(docx_file)
    
    # 최근 DOCX가 없으면 다운로드 버튼 표시 안함
    if not recent_docx:
        return
    
    # 보고서 이름에서 topic 번호 추출 (예: "Topic_0_센서_전력.md" -> "0")
    import re
    topic_match = re.search(r'Topic_(\d+)', report_name)
    if not topic_match:
        return
    
    topic_num = topic_match.group(1)
    
    # 최근 DOCX 파일 중에서 해당 topic 번호와 일치하는 파일 찾기
    matching_docx = None
    for docx_file in recent_docx:
        docx_name = os.path.basename(docx_file)
        if f"{topic_num}_Topic_{topic_num}" in docx_name:
            matching_docx = docx_file
            break
    
    if matching_docx:
        docx_name = os.path.basename(matching_docx)
        try:
            with open(matching_docx, "rb") as f:
                docx_data = f.read()
            
            st.download_button(
                label="📄 DOCX 다운로드",
                data=docx_data,
                file_name=docx_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="secondary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"DOCX 파일 로드 실패: {str(e)}")

def display_single_docx_download(report_name):
    """선택된 보고서에 해당하는 DOCX 다운로드 버튼만 표시 (최근 분석 결과만)"""
    found_docx_dir, docx_files = get_recent_docx_files()
    
    if not found_docx_dir or not docx_files:
        return
    
    # 최근 10분 이내에 생성된 DOCX 파일만 필터링 (방금 완료한 분석만)
    from datetime import datetime
    current_time = datetime.now()
    recent_docx = []
    
    for docx_file in docx_files:
        file_time = datetime.fromtimestamp(os.path.getmtime(docx_file))
        time_diff = (current_time - file_time).total_seconds() / 60  # 분 단위
        if time_diff <= 10:  # 10분 이내만
            recent_docx.append(docx_file)
    
    # 최근 DOCX가 없으면 다운로드 버튼 표시 안함
    if not recent_docx:
        st.info("💡 방금 완료한 분석의 보고서만 DOCX 다운로드가 가능합니다.")
        return
    
    # 보고서 이름에서 topic 번호 추출 (예: "Topic_0_센서_전력.md" -> "0")
    import re
    topic_match = re.search(r'Topic_(\d+)', report_name)
    if not topic_match:
        return
    
    topic_num = topic_match.group(1)
    
    # 최근 DOCX 파일 중에서 해당 topic 번호와 일치하는 파일 찾기
    matching_docx = None
    for docx_file in recent_docx:
        docx_name = os.path.basename(docx_file)
        if f"{topic_num}_Topic_{topic_num}" in docx_name:
            matching_docx = docx_file
            break
    
    if matching_docx:
        docx_name = os.path.basename(matching_docx)
        try:
            with open(matching_docx, "rb") as f:
                docx_data = f.read()
            
            st.download_button(
                label="📄 DOCX 다운로드",
                data=docx_data,
                file_name=docx_name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="secondary",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"DOCX 파일 로드 실패: {str(e)}")
    else:
        st.info("💡 이 보고서는 최근 분석 결과가 아닙니다. DOCX 다운로드는 방금 완료한 분석만 가능합니다.")

def get_recent_docx_files():
    """최근 생성된 DOCX 파일들을 가져오는 함수"""
    docx_dir = "reports_docx.v8"
    
    # 상대 경로와 절대 경로 모두 확인
    possible_paths = [
        docx_dir,
        f"./code/{docx_dir}",
        f"/Users/shinseungmin/Documents/벌토픽_전체코드/{docx_dir}",
        f"code/{docx_dir}"
    ]
    
    found_docx_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            found_docx_dir = path
            break
    
    if not found_docx_dir:
        return None, []
    
    docx_files = glob.glob(os.path.join(found_docx_dir, "*.docx"))
    return found_docx_dir, docx_files

def display_docx_download_section():
    """최근 분석 완료된 DOCX 파일 다운로드 섹션"""
    st.subheader("📄 DOCX 보고서 다운로드")
    
    found_docx_dir, docx_files = get_recent_docx_files()
    
    if not found_docx_dir or not docx_files:
        st.info("📄 DOCX 보고서가 아직 생성되지 않았습니다.")
        return
    
    # 최근 10분 이내에 생성된 DOCX 파일만 필터링
    current_time = datetime.now()
    recent_docx = []
    
    for docx_file in docx_files:
        file_time = datetime.fromtimestamp(os.path.getmtime(docx_file))
        time_diff = (current_time - file_time).total_seconds() / 60  # 분 단위
        if time_diff <= 10:  # 10분 이내
            recent_docx.append(docx_file)
    
    # 최신 순으로 정렬
    recent_docx.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    if not recent_docx:
        # 최근 DOCX가 없으면 최신 7개만 표시
        docx_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        recent_docx = docx_files[:7]
        st.info("💡 최근 생성된 DOCX 보고서들을 표시합니다.")
    
    if recent_docx:
        st.write(f"📊 **{len(recent_docx)}개**의 DOCX 보고서가 준비되었습니다:")
        
        # DOCX 파일들을 2열로 배치
        cols = st.columns(2)
        for i, docx_file in enumerate(recent_docx):
            file_name = os.path.basename(docx_file)
            file_time = datetime.fromtimestamp(os.path.getmtime(docx_file))
            
            with cols[i % 2]:
                with st.container():
                    st.markdown(f"**📄 {file_name}**")
                    st.caption(f"생성: {file_time.strftime('%Y-%m-%d %H:%M')}")
                    
                    # 다운로드 버튼
                    try:
                        with open(docx_file, "rb") as f:
                            docx_data = f.read()
                        
                        st.download_button(
                            label="📥 다운로드",
                            data=docx_data,
                            file_name=file_name,
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key=f"download_{i}_{file_name}",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"파일 읽기 오류: {str(e)}")
        
        # 전체 다운로드 버튼
        st.markdown("---")
        if st.button("📦 모든 DOCX 파일 ZIP으로 다운로드", type="primary", use_container_width=True):
            try:
                import zipfile
                from io import BytesIO
                
                # ZIP 파일 생성
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for docx_file in recent_docx:
                        file_name = os.path.basename(docx_file)
                        zip_file.write(docx_file, file_name)
                
                zip_data = zip_buffer.getvalue()
                
                # ZIP 다운로드 버튼
                st.download_button(
                    label="📦 ZIP 파일 다운로드",
                    data=zip_data,
                    file_name=f"analysis_reports_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    key="download_all_zip"
                )
                
            except Exception as e:
                st.error(f"ZIP 파일 생성 중 오류: {str(e)}")

def display_current_analysis_reports():
    """현재 분석에 대한 보고서만 표시 (최신 보고서들)"""
    st.subheader("📋 방금 완료한 분석 보고서")
    
    found_reports_dir, report_files = get_report_files()
    
    if not found_reports_dir or not report_files:
        st.warning("📋 기술 보고서가 아직 생성되지 않았습니다.")
        st.info("💡 토픽 분석을 완료하면 자동으로 AI 기술 보고서가 생성됩니다.")
        return
    
    # 최근 10분 이내에 생성된 보고서만 필터링 (현재 분석 결과)
    current_time = datetime.now()
    recent_reports = []
    
    for report_file in report_files:
        file_time = datetime.fromtimestamp(os.path.getmtime(report_file))
        time_diff = (current_time - file_time).total_seconds() / 60  # 분 단위
        if time_diff <= 10:  # 10분 이내
            recent_reports.append(report_file)
    
    # 최신 순으로 정렬
    recent_reports.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    if not recent_reports:
        # 최근 보고서가 없으면 최신 보고서 5개만 표시
        report_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        recent_reports = report_files[:5]
        st.info("💡 최근 생성된 보고서 5개를 표시합니다.")
    
    # 보고서 선택
    report_names = [os.path.basename(f) for f in recent_reports]
    selected_report = st.selectbox("보고서 선택:", report_names, key="current_analysis_reports")
    
    if selected_report:
        report_path = os.path.join(found_reports_dir, selected_report)
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 보고서 제목과 다운로드 버튼을 같은 줄에 배치
            col1, col2 = st.columns([3, 1])
            with col1:
                # 보고서 제목 추출 (첫 번째 줄에서)
                first_line = content.split('\n')[0] if content else selected_report
                if first_line.startswith('#'):
                    display_title = first_line.replace('#', '').strip()
                else:
                    display_title = selected_report.replace('.md', '')
                st.markdown(f"### 📋 {display_title}")
            
            with col2:
                # 선택된 보고서에 해당하는 개별 DOCX 다운로드 버튼 표시
                display_single_docx_download_for_analysis(selected_report)
            
            st.markdown(content)
        except Exception as e:
            st.error(f"보고서를 읽는 중 오류 발생: {str(e)}")

def display_generated_reports():
    """결과 페이지에서 현재 분석 보고서 표시 (기존 함수 대체)"""
    display_current_analysis_reports()

def get_topic_title_from_report(topic_num):
    """보고서 파일에서 토픽 제목 추출"""
    found_reports_dir, report_files = get_report_files()
    
    if not found_reports_dir or not report_files:
        return None
    
    # 해당 토픽 번호의 보고서 파일 찾기
    for report_file in report_files:
        file_name = os.path.basename(report_file)
        if f"Topic_{topic_num}_" in file_name:
            try:
                with open(report_file, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    # "# Topic X: 제목" 형식에서 제목 부분 추출
                    if first_line.startswith(f"# Topic {topic_num}:"):
                        title = first_line.replace(f"# Topic {topic_num}:", "").strip()
                        return title
            except Exception:
                continue
    return None

def get_topic_patents(topic_num):
    """토픽에 해당하는 특허 정보를 반환"""
    try:
        import pandas as pd
        import os
        
        # extract_end.csv 파일에서 특허 데이터 읽기
        if not os.path.exists("./extract_end.csv"):
            return []
            
        df = pd.read_csv("./extract_end.csv")
        
        # 토픽 키워드 가져오기
        if 'topic_results' in st.session_state and st.session_state.topic_results:
            topic_keywords = st.session_state.topic_results.get(topic_num, [])
            if not topic_keywords:
                return []
            
            # 상위 5개 키워드로 특허 필터링
            top_keywords = topic_keywords[:5]
            
            # 키워드가 포함된 특허들 찾기
            matched_patents = []
            for _, patent in df.iterrows():
                # 발명명칭과 요약에서 키워드 매칭 확인
                title = str(patent.get('발명명칭', ''))
                abstract = str(patent.get('astrtCont', ''))
                search_text = (title + ' ' + abstract).lower()
                
                # 키워드 중 하나라도 포함되어 있으면 매칭
                if any(keyword.lower() in search_text for keyword in top_keywords):
                    patent_info = {
                        'applicant': patent.get('출원인', 'N/A'),
                        'title': patent.get('발명명칭', 'N/A'),
                        'application_date': patent.get('출원일', 'N/A')
                    }
                    matched_patents.append(patent_info)
            
            # 중복 제거 및 최대 10개로 제한
            seen = set()
            unique_patents = []
            for patent in matched_patents:
                key = (patent['applicant'], patent['title'])
                if key not in seen and len(unique_patents) < 10:
                    seen.add(key)
                    unique_patents.append(patent)
            
            return unique_patents
            
    except Exception as e:
        print(f"특허 정보 로드 오류: {e}")
        return []
    
    return []

def find_docx_file(topic_num):
    """해당 토픽의 워드 파일 찾기"""
    docx_dir = "reports_docx.v8"
    
    # 상대 경로와 절대 경로 모두 확인
    possible_paths = [
        docx_dir,
        f"./code/{docx_dir}",
        f"/Users/shinseungmin/Documents/벌토픽_전체코드/{docx_dir}",
        f"code/{docx_dir}"
    ]
    
    found_docx_dir = None
    for path in possible_paths:
        if os.path.exists(path):
            found_docx_dir = path
            break
    
    if not found_docx_dir:
        return None
    
    # 해당 토픽 번호의 워드 파일 찾기
    docx_files = glob.glob(os.path.join(found_docx_dir, "*.docx"))
    for docx_file in docx_files:
        file_name = os.path.basename(docx_file)
        if file_name.startswith(f"{topic_num}_Topic_{topic_num}_"):
            return docx_file
    
    return None

def display_topic_report(topic_num):
    """특정 토픽의 보고서 표시"""
    found_reports_dir, report_files = get_report_files()
    
    if not found_reports_dir or not report_files:
        st.error("보고서 파일을 찾을 수 없습니다.")
        return
    
    # 해당 토픽 번호의 보고서 파일 찾기
    target_report = None
    for report_file in report_files:
        file_name = os.path.basename(report_file)
        if f"Topic_{topic_num}_" in file_name:
            target_report = report_file
            break
    
    if not target_report:
        st.error(f"Topic {topic_num}에 대한 보고서를 찾을 수 없습니다.")
        return
    
    try:
        # 워드 파일 다운로드 버튼 추가
        docx_file = find_docx_file(topic_num)
        if docx_file:
            col1, col2 = st.columns([4, 1])
            with col2:
                try:
                    with open(docx_file, "rb") as file:
                        docx_data = file.read()
                    
                    file_name = os.path.basename(docx_file)
                    st.download_button(
                        label="📥 워드파일 다운로드",
                        data=docx_data,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"워드 파일을 읽는 중 오류: {e}")
        
        with open(target_report, "r", encoding="utf-8") as f:
            content = f.read()
        
        # 마크다운 내용을 streamlit에 표시
        st.markdown(content)
        
    except Exception as e:
        st.error(f"보고서를 읽는 중 오류가 발생했습니다: {e}")

def display_topic_results():
    """토픽 분석 결과 표시"""
    if st.session_state.topic_results:
        st.subheader("🔍 토픽 분석 결과")
        
        # 토픽 개수 정보 표시
        topic_count = len(st.session_state.topic_results)
        st.info(f"📊 총 **{topic_count}개**의 주요 토픽이 발견되었습니다.")
        
        # 선택된 토픽이 있으면 보고서 표시
        if st.session_state.selected_topic is not None:
            display_topic_report(st.session_state.selected_topic)
            if st.button("⬅️ 토픽 목록으로 돌아가기"):
                st.session_state.selected_topic = None
                st.rerun()
            return
        
        # 토픽들을 번호 순으로 정렬하여 표시
        sorted_topics = sorted(st.session_state.topic_results.items(), key=lambda x: int(x[0]) if str(x[0]).isdigit() else float('inf'))
        
        for topic_id, words in sorted_topics:
            # topic_id가 문자열일 수 있으므로 int로 변환 후 처리
            try:
                topic_num = int(topic_id)
                display_topic_id = topic_num if topic_num >= 0 else "Noise"
                
                # 보고서에서 토픽 제목 가져오기
                topic_title = get_topic_title_from_report(topic_num) if topic_num >= 0 else None
                
                if topic_title:
                    expander_title = f"Topic {display_topic_id}: {topic_title}"
                else:
                    expander_title = f"Topic {display_topic_id}"
                    
            except (ValueError, TypeError):
                display_topic_id = str(topic_id)
                expander_title = f"Topic {display_topic_id}"
                
            # expander를 사용해서 즉시 키워드 표시 (딜레이 없음)
            with st.expander(expander_title, expanded=False):
                # 토픽 이름을 클릭하면 보고서 표시하는 버튼
                if st.button(f"📋 {expander_title} 보고서 보기", key=f"topic_report_{topic_id}", use_container_width=True):
                    st.session_state.selected_topic = topic_num if isinstance(topic_num, int) and topic_num >= 0 else None
                    st.rerun()
                
                st.markdown("**주요 키워드:**")
                if isinstance(words, list) and len(words) > 0:
                    # 키워드를 더 보기 좋게 표시
                    keywords_text = ", ".join(words[:10])  # 상위 10개 키워드 표시
                    st.write(keywords_text)
                    st.caption("상위 10개 주요키워드 표시")
                else:
                    st.write("키워드 정보가 없습니다.")
                
                # 관련 특허 정보 표시
                st.markdown("---")
                st.markdown("**관련 특허 정보:**")
                
                try:
                    topic_patents = get_topic_patents(topic_num if isinstance(topic_num, int) and topic_num >= 0 else -1)
                    
                    if topic_patents:
                        st.caption(f"이 보고서 작성에 사용된 주요 특허 {len(topic_patents)}건")
                        
                        for i, patent in enumerate(topic_patents, 1):
                            with st.expander(f"📄 {i}. {patent.get('title', 'N/A')[:60]}{'...' if len(patent.get('title', '')) > 60 else ''}"):
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.markdown(f"**📋 특허명:** {patent.get('title', 'N/A')}")
                                    st.markdown(f"**👤 출원인:** {patent.get('applicant', 'N/A')}")
                                    
                                with col2:
                                    st.markdown(f"**📅 출원일:** {patent.get('application_date', 'N/A')}")
                                
                                # 추가 정보가 있다면 표시
                                if patent.get('abstract'):
                                    st.markdown("**📝 요약:**")
                                    st.write(patent.get('abstract', '')[:200] + '...' if len(patent.get('abstract', '')) > 200 else patent.get('abstract', ''))
                                
                                if patent.get('ipc_class'):
                                    st.markdown(f"**🏷️ IPC 분류:** {patent.get('ipc_class', 'N/A')}")
                    else:
                        st.info("💡 해당 토픽과 관련된 특허 정보를 찾을 수 없습니다.")
                        
                except Exception as e:
                    st.error(f"특허 정보 로드 중 오류가 발생했습니다: {str(e)}")
                    
    else:
        st.warning("🔍 토픽 분석이 아직 완료되지 않았습니다.")
        st.info("💡 **완전한 토픽 분석을 위해서는** 위의 특허 동향 그래프를 확인한 후, 원하는 날짜 범위를 선택하고 **'🚀 완전한 토픽 분석 실행'** 버튼을 클릭하세요.")
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
    
    # 페이지 라우팅
    if st.session_state.current_page == "home":
        show_home_page()
    elif st.session_state.current_page == "results":
        show_results_page()

def show_home_page():
    """홈 페이지 표시"""
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
        # 로고 표시 (사이드바 상단)
        show_sidebar_logo()
        
        st.header("🚀 키워드 분석 시작")
        
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
                # 분석 완료 후 결과 페이지로 이동
                if st.session_state.analysis_complete:
                    st.session_state.current_page = "results"
                    st.rerun()
        
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
        
        # 보고서 선택 (사이드바)
        st.markdown("---")
        display_sidebar_reports()
        
        # 홈 버튼을 사이드바 하단에 배치
        show_sidebar_footer()
        
    
    # 메인 컨텐츠 영역 (완전한 초기 상태일 때)
    if (st.session_state.step_progress == 0 and 
        not st.session_state.analysis_complete and 
        not st.session_state.waiting_for_date_input):
        # 탭 생성
        tab1, tab2 = st.tabs(["🏠 메인", "📋 보고서"])
        
        # 탭 텍스트 크기 조정
        st.markdown("""
        <style>
        .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
            font-size: 1.2rem !important;
            font-weight: 600 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with tab1:
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
        
        with tab2:
            # 선택된 보고서 표시 (보고서 탭)
            display_selected_report()
    
    elif st.session_state.waiting_for_date_input:
        # Step 3.5 완료 후 날짜 입력 대기 화면
        st.markdown("## 🎯 특허 동향 그래프 생성 완료!")
        
        # 그래프 표시
        display_patent_graph()
        
        st.markdown("---")
        st.markdown("## 📅 분석 날짜 범위 선택")
        st.write("위 그래프를 참고하여 더 자세히 분석하고 싶은 날짜 범위를 선택하세요.")
        
        st.info("""
        💡 **날짜 범위 선택 후 완전한 토픽 분석을 실행합니다:**
        - 🚀 **BERTopic 분석 + AI 보고서 생성**: 선택한 날짜 범위의 데이터로 완전한 분석 수행
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
            if st.button("🚀 완전한 토픽 분석 실행", type="primary", use_container_width=True):
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
                        result = continue_analysis_from_step4()
                        
                        # 분석 완료 후 결과 페이지로 이동
                        if st.session_state.analysis_complete:
                            st.session_state.current_page = "results"
                            st.rerun()
                else:
                    st.error("❌ 시작 연도가 종료 연도보다 클 수 없습니다.")
            
        
        # 날짜 범위 미리보기
        if start_year and end_year and start_year <= end_year:
            try:
                df = pd.read_csv("./extract_end.csv")
                
                # openDate가 있는 데이터만 사용 (step3_5_특허그래프.py와 동일한 방식)
                df = df.dropna(subset=['openDate'])
                df["openDate"] = df["openDate"].astype(str).str.replace('.0', '').str.strip()
                df["출원연도"] = pd.to_datetime(
                    df["openDate"], format='%Y%m%d', errors="coerce"
                ).dt.year
                df = df.dropna(subset=['출원연도'])
                
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
    
def show_results_page():
    """분석 결과 페이지 표시"""
    # 분석 완료 화면
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 🎉 분석 완료!")
    
    # 사이드바에 분석 정보 표시
    with st.sidebar:
        # 로고 표시 (사이드바 상단)
        show_sidebar_logo()
        
        st.success("✅ 분석 완료!")
        st.write(f"**키워드:** {st.session_state.keyword_input}")
        
        if hasattr(st.session_state, 'selected_date_range') and st.session_state.selected_date_range:
            date_info = st.session_state.selected_date_range
            st.write(f"**기간:** {date_info['start_year']}-{date_info['end_year']}")
            st.write(f"**분석 건수:** {date_info['filtered_count']}건")
        
        if st.button("🔄 새 분석 시작", type="secondary"):
            st.session_state.current_page = "home"
            st.session_state.analysis_complete = False
            st.session_state.step_progress = 0
            st.session_state.topic_results = None
            st.session_state.waiting_for_date_input = False
            st.session_state.date_filtered = False
            st.rerun()
        
        # 홈 버튼을 사이드바 하단에 배치
        show_sidebar_footer()
    
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
    tab1, tab2, tab3 = st.tabs(["📈 특허 동향 그래프", "📊 토픽 분석 결과", "🖼️ 시각화"])
    
    with tab1:
        display_patent_graph()
    
    with tab2:
        display_topic_results()
    
    with tab3:
        display_topic_visualization()

if __name__ == "__main__":
    main()