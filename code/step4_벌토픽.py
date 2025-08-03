import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

# Compatibility patch for scipy.linalg.triu issue
import numpy as np
import scipy.linalg
if not hasattr(scipy.linalg, 'triu'):
    scipy.linalg.triu = np.triu

# Compatibility patch for huggingface_hub
try:
    from huggingface_hub import cached_download
except ImportError:
    from huggingface_hub import hf_hub_download as cached_download
    import huggingface_hub
    huggingface_hub.cached_download = cached_download

from tqdm import tqdm
import itertools
from umap import UMAP
from hdbscan import HDBSCAN
from bertopic import BERTopic
from gensim.corpora import Dictionary
from gensim.models.coherencemodel import CoherenceModel
import os
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch
from bertopic import BERTopic
import umap.umap_ as umap
import torch
import random
from torch import nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from tqdm import tqdm, tqdm_notebook
from torch.optim import AdamW
from transformers.optimization import get_cosine_schedule_with_warmup
from kobert_transformers import get_kobert_model
import nltk
from itertools import product
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk import pos_tag
from sklearn.preprocessing import normalize
import pandas as pd
# Java 불필요한 한국어 NLP 라이브러리 사용
try:
    from kiwipiepy import Kiwi
    USE_KIWI = True
except ImportError:
    try:
        from konlpy.tag import Okt
        USE_KIWI = False
    except ImportError:
        USE_KIWI = None
from transformers import BertModel, BertTokenizer
from transformers import AutoModel
from bertopic import BERTopic
from bertopic.vectorizers import ClassTfidfTransformer
from sklearn.feature_extraction.text import CountVectorizer
try:
    from ugtm import eGTM
except ImportError:
    eGTM = None
    print("Warning: ugtm not available due to compatibility issues")
import umap
import hdbscan
import re

class Step4:
    def ber(self):
        nltk.download('punkt')
        nltk.download('wordnet')
        nltk.download('stopwords')
        nltk.download('averaged_perceptron_tagger')

        file_path = './extract_end.csv'
        patent = pd.read_csv(file_path)

        summ = patent['astrtCont']+patent['발명명칭']
        #summ=patent['청구항']
        #print(summ)
        # 표제어 추출기 설정
        lemmatizer = WordNetLemmatizer()


        def wordnet_pos_tags_kor(treebank_tag):
            """Converts POS tags from Korean treebank format to WordNet format."""
            if treebank_tag.startswith('VA') or treebank_tag.startswith('VV'):
                return 'v'  # verb
            elif treebank_tag.startswith('N'):
                return 'n'  # noun
            elif treebank_tag.startswith('M'):
                return 'r'  # adverb (관형사, 부사)
            elif treebank_tag.startswith('XR') or treebank_tag.startswith('MM'):
                return 'a'  # adjective (어근, 관형사)
            else:
                return 'n'  # default to noun

        # 한국어 NLP 라이브러리 초기화
        if USE_KIWI:
            kiwi = Kiwi()
            print("✅ Kiwi 형태소 분석기 사용 (Java 불필요)")
        elif USE_KIWI == False:
            try:
                okt = Okt()
                print("✅ KoNLPy Okt 형태소 분석기 사용")
            except Exception as e:
                print(f"⚠️ KoNLPy 초기화 실패 (Java 환경 문제): {e}")
                print("💡 해결 방법:")
                print("   pip install kiwipiepy  # Java 불필요한 대안")
                print("   또는 Java 환경 설정 필요")
                raise RuntimeError("한국어 형태소 분석기를 사용할 수 없습니다.")
        else:
            print("⚠️ 한국어 형태소 분석기를 사용할 수 없습니다. kiwipiepy 또는 konlpy를 설치하세요.")
            raise RuntimeError("한국어 형태소 분석기가 없습니다.")

        # 0.1) 불용어 목록 로드
        with open('data/stopwords.txt', 'r', encoding='utf-8') as f:
            stop_words = set(f.read().splitlines())

        # 0.2) 영어 키워드 로드 → 모두 소문자로 통일
        with open('data/eng_data.txt', 'r', encoding='utf-8') as f:
            eng_keywords = set(line.strip().lower() for line in f if line.strip())

        # 0.3) 복합 키워드(raw_phrases) 로드 → 소문자 키, 소문자 값(glued)으로 통일
        with open('data/phrase_data.txt', 'r', encoding='utf-8') as f:
            raw_phrases = [line.strip() for line in f if line.strip()]

        # 길이가 긴 순서대로 정렬한 뒤, 키와 값을 모두 소문자로 바꿔서 저장
        raw_phrases.sort(key=len, reverse=True)
        concat_phrases = {
            ph.lower(): ph.replace(' ', '').lower()
            for ph in raw_phrases
        }

        # ───────────────────────────────────────────────────────────────
        # 1) 원본 “청구항” 리스트(summ)에서 실제로 등장한 복합어·영어 키워드만 추려내기
        # ───────────────────────────────────────────────────────────────

        # used_phrases : 전처리 이전 원문에 포함된 glue(composite) 복합어 집합
        # used_eng     : 전처리 이전 원문에 포함된 영어 키워드 집합
        used_phrases = set()
        used_eng     = set()

        for summary in summ:
            if not isinstance(summary, str):
                continue

            lower = summary.lower()

            # 1.1) 복합어 등장 체크 (소문자 키 기준, IGNORECASE 안전장치)
            for ph_lower, glued_lower in concat_phrases.items():
                if re.search(re.escape(ph_lower), lower, flags=re.IGNORECASE):
                    used_phrases.add(glued_lower)

            # 1.2) 영어 키워드 등장 체크
            for w in re.findall(r'\b[a-zA-Z]+\b', lower):
                lw = w.lower()
                if lw in eng_keywords:
                    used_eng.add(lw)

        # ───────────────────────────────────────────────────────────────
        # 2) 전처리 함수: 복합어 치환 → 불용어 제거 → 형태소 분석용 토큰화
        # ───────────────────────────────────────────────────────────────

        def preprocess_patent_summaries(summaries):
            preprocessed_summaries = []

            for summary in summaries:
                if not isinstance(summary, str):
                    preprocessed_summaries.append("")
                    continue

                text = summary

                # 2.1) 보호할 복합어(glued) 치환 (key=ph_lower, value=glued_lower 모두 소문자)
                #     → IGNORECASE로 대소문자 무시하며 치환
                for ph_lower, glued_lower in concat_phrases.items():
                    text = re.sub(re.escape(ph_lower), glued_lower, text, flags=re.IGNORECASE)

                # 2.2) 치환된 복합어를 등장 횟수만큼 수집 (사후 처리 위해)
                found_phrases = []
                for ph_lower, glued_lower in concat_phrases.items():
                    # text도 소문자 변환해서 검사하면 안전하지만, 이미 위 치환에서 한 번 처리됨
                    count = len(re.findall(re.escape(glued_lower), text, flags=re.IGNORECASE))
                    if count:
                        found_phrases.extend([glued_lower] * count)

                # 2.3) 영어 키워드를 등장 횟수만큼 수집
                raw_eng = re.findall(r'\b[a-zA-Z]+\b', text)
                kept_eng = []
                for w in raw_eng:
                    lw = w.lower()
                    if lw in eng_keywords:
                        kept_eng.append(lw)

                # 2.4) 한글과 공백만 남기기 (숫자가 필요 없으면 제거)
                kor_only = re.sub(r'[^가-힣\s]', ' ', text)
                kor_only = re.sub(r'\s+', ' ', kor_only).strip()

                # 2.5) 형태소 분석 → 불용어 제거
                if USE_KIWI:
                    # Kiwi는 tokenize() 메서드를 사용하고 form을 추출
                    tokens = [token.form for token in kiwi.tokenize(kor_only)]
                else:
                    tokens = okt.morphs(kor_only, stem=True)
                tokens = [t for t in tokens if t not in stop_words]

                components = set()
                for ph_lower, glued_lower in concat_phrases.items():
                    if re.search(re.escape(glued_lower), text, flags=re.IGNORECASE):
                        # ⟶ ph_lower에 공백이 있었다면 ph_lower.split()으로 분리된 단어들을 components에 추가하는 기존 방식 대신
                        #     glued_lower(공백 없는 형태)만 components로 두면, “아웃바운드” 자체만 제거 대상이 됨.
                        components.add(glued_lower)

                # 2.7) components에 포함된 토큰 제거
                tokens = [t for t in tokens if t not in components]

                # 2.8) 보호된 복합어·영어 키워드 횟수만큼 재추가
                tokens.extend(found_phrases)
                tokens.extend(kept_eng)

                preprocessed_summaries.append(" ".join(tokens))

            return preprocessed_summaries

        def extract_lemmatized_tokens(pre_docs):
            """
            pre_docs : preprocess_patent_summaries를 통과한 문장 문자열 리스트

            내부에서 전역 변수 concat_phrases, eng_keywords를 참조하여,
            Okt가 분리한 복합어 하위 토큰 제거 후, 복합어 전체만 남김.
            """
            lemmatized_docs = []

            for doc in pre_docs:
                text = doc if isinstance(doc, str) else ""

                # 3.1) 형태소 태깅
                if USE_KIWI:
                    # Kiwi의 경우 pos() 메서드 사용
                    tokens_with_pos = [(token.form, token.tag) for token in kiwi.tokenize(text)]
                else:
                    tokens_with_pos = okt.pos(text, stem=True)

                # 3.2) 복합어(glued) 등장 횟수만큼 수집
                found_phrases = []
                for ph_lower, glued_lower in concat_phrases.items():
                    count = len(re.findall(re.escape(glued_lower), text, flags=re.IGNORECASE))
                    if count:
                        found_phrases.extend([glued_lower] * count)

                # 3.3) 중간 표제어 수집
                lem = []
                for token, tag in tokens_with_pos:
                    # 3.3.1) 영어 키워드(소문자)인 경우
                    if token.lower() in eng_keywords:
                        lem.append(token)
                        continue

                    # 3.3.2) Okt가 통째로 인식한 복합어인 경우 (예: "아웃바운드")
                    #        ⟶ concat_phrases.values()는 모두 소문자 glue 형태임.
                    if token.lower() in concat_phrases.values():
                        lem.append(token)
                        continue

                    # 3.3.3) 일반 명사/동사/형용사/영문 알파벳 태그인 경우
                    if wordnet_pos_tags_kor(tag):
                        lem.append(token)
                        continue

                    # 그 외는 버림

                # 3.4) cleanup: 복합어 일부로 분리된 하위 토큰(예: "아웃", "바운드") 제거
                cleaned = []
                for token in lem:
                    is_subpart = False
                    for glued_lower in found_phrases:
                        # token이 glued_lower(예: "아웃바운드") 하위 문자열인지 검사
                        if token.lower() in glued_lower:
                            is_subpart = True
                            break
                    if not is_subpart:
                        cleaned.append(token)

                # 3.5) 복합어 전체(glued) 등장 횟수만큼 다시 추가
                cleaned.extend(found_phrases)

                # 3.6) 최종 저장
                lemmatized_docs.append(" ".join(cleaned).strip())

            return lemmatized_docs

        # 특허 요약문 전처리
        patent_prep = preprocess_patent_summaries(summ)
        #print(patent_prep)

        # 4.4) 표제어(lemma) 추출: 복합어 분리 방지 로직
        lemmatized_patents = extract_lemmatized_tokens(patent_prep)
        #print(f'len:{len(lemmatized_patents)}')
        
        # 데이터 검증: 빈 데이터 확인
        if not lemmatized_patents:
            print("❌ 전처리된 특허 데이터가 없습니다.")
            return {}
        
        # 빈 문서들 제거
        lemmatized_patents = [doc for doc in lemmatized_patents if doc.strip()]
        
        if not lemmatized_patents:
            print("❌ 유효한 전처리된 특허 데이터가 없습니다.")
            return {}
        
        print(f"✅ {len(lemmatized_patents)}개의 전처리된 문서로 토픽 모델링을 진행합니다.")

        # 4.5) all_tokens 생성
        all_tokens = set()
        for doc in lemmatized_patents:
            all_tokens.update(doc.split())

        # 4.5) 최종 vocab 생성: used_phrases ∪ used_eng ∪ all_tokens – stop_words
        vocab = (used_phrases | used_eng | all_tokens) - set(stop_words)

        """#### 보호 단어 확인"""

        # 5.1) lowercased all_tokens 집합
        all_tokens_lower = {tok.lower() for tok in all_tokens}

        # 5.2) eng_keywords 집합과 교집합 확인
        protected_eng_in_all = all_tokens_lower.intersection(eng_keywords)

        for idx, doc in enumerate(lemmatized_patents):
            tokens = doc.split()

        seed = 42

        # Python 내장 랜덤 모듈 시드 설정
        random.seed(seed)

        # NumPy 시드 설정
        np.random.seed(seed)

        # PyTorch 시드 설정
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)

        # ─── 0. Pretendard TTF 파일을 Matplotlib에 등록하여 폰트 이름 추출 ─────────────
        import os
        import matplotlib.font_manager as fm
        # PretendardVariable.ttf 파일 경로 (본인 환경에 맞춰 수정)
        font_path = "data/Pretendard-1.3.9/public/variable/PretendardVariable.ttf"
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Pretendard TTF 파일을 찾을 수 없습니다: {font_path}")
        # Matplotlib font_manager를 통해 Pretendard를 등록
        fm.fontManager.addfont(font_path)
        # 실제 폰트 패밀리 이름을 가져옵니다. Ex) "Pretendard Variable"
        pret_name = fm.FontProperties(fname=font_path).get_name()



        mpl.rcParams['font.family'] = pret_name
        mpl.rcParams['axes.unicode_minus'] = False   # 한글 사용 시 마이너스 깨짐 방지
        from sentence_transformers import SentenceTransformer
        # Hugging Face 429 에러 임시 해결책 - 다른 모델 사용
        try:
            embedding_model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")
        except Exception as e:
            print(f"KR-SBERT 모델 로드 실패, 대체 모델 사용: {e}")
            # 대체 모델 사용
            embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        # lemmatized_patents: 이미 전처리가 끝난 특허 텍스트 리스트 (예: ["문서1", "문서2", ...])
        embeddings = embedding_model.encode(
            lemmatized_patents,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        # embeddings.shape == (문서 수, 임베딩 차원)

        # ─── 3. 2D 전용 UMAP 투영 ────────────────────────────────────────────────────
        umap_2d = umap.UMAP(
            n_neighbors=15,
            n_components=2,  # 2차원으로 축소 (시각화용)
            metric='cosine',
            min_dist=0.1,
            random_state=42
        )
        umap_embeddings_2d = umap_2d.fit_transform(embeddings)
        # umap_embeddings_2d.shape == (문서 수, 2)

        # ─── 4. BERTopic으로부터 토픽(label) 정보 가져오기 ──────────────────────────────
        # 이미 학습된 topic_model 객체가 메모리에 올라와 있어야 합니다.
        # 예: topic_model = BERTopic(...); topics, probabilities = topic_model.fit_transform(lemmatized_patents)

        topic_model = BERTopic(
            embedding_model=embedding_model,
            umap_model=umap_2d  # 기존에 만든 umap_2d 사용
        )
        #print(f'check:{lemmatized_patents}')
        topics, probabilities = topic_model.fit_transform(lemmatized_patents)
        # topics: 길이 == 문서 수, 예) [0, 2, 1, 1, -1, 3, …]

        # ─── 5. 사용자 지정 토픽별 색상 매핑 ─────────────────────────────────────────
        # 토픽 0~5와 노이즈(-1)를 위한 색상 딕셔너리
        topic_to_color = {
            0: "#8dd3c7",  # Topic 0 → 연한 청록
            1: "#4eb3d3",  # Topic 1 → 중간 톤 파랑
            2: "#08589e",  # Topic 2 → 진한 남색
            3: "#fdb462",  # Topic 3 → 연한 주황
            4: "#fb8072",  # Topic 4 → 부드러운 코랄 레드
            5: "#b30000",  # Topic 5 → 진한 붉은 주황
            -1: (0.50, 0.50, 0.50, 0.6)  # Topic -1 (노이즈) → 연회색 투명
        }

        # 문서별 할당된 토픽 번호로 색상 리스트 생성
        point_colors = [topic_to_color.get(t, 'lightgray') for t in topics]

        # ─── 6. 2D UMAP 위에 토픽별 산점도 그리기 ────────────────────────────────────
        plt.figure(figsize=(14, 10))
        plt.scatter(
            umap_embeddings_2d[:, 0],  # x축 좌표
            umap_embeddings_2d[:, 1],  # y축 좌표
            c=point_colors,  # 토픽별 사용자 지정 색상
            s=70,  # 점 크기
            alpha=0.6,  # 투명도
            edgecolor='none'
        )

        # ─── 7. 토픽 중심(centroid)에 “Topic {번호}”만 표시 ──────────────────────────────
        for t in [0, 1, 2, 3, 4, 5]:
            # 해당 토픽 t에 속한 문서들의 인덱스만 모읍니다.
            indices = [i for i, topic_id in enumerate(topics) if topic_id == t]
            if len(indices) == 0:
                continue  # 해당 토픽에 문서가 없으면 건너뜁니다.

            cluster_points = umap_embeddings_2d[indices]
            centroid = cluster_points.mean(axis=0)

            # “Topic {번호}”만 표시
            label_text = f"Topic {t}"

            plt.text(
                centroid[0], centroid[1], label_text,
                fontsize=12,
                weight='bold',
                color='black',
                ha='center',
                va='center',
                bbox=dict(
                    facecolor='white',
                    alpha=0.7,
                    edgecolor='gray',
                    linewidth=0.5,
                    boxstyle='round,pad=0.3'
                )
            )

        # ─── 8. 범례(Legend) 생성 ──────────────────────────────────────────────────
        legend_handles = [
            Patch(facecolor=topic_to_color[-1], edgecolor='none', label="Topic –1 (Noise)"),
            Patch(facecolor=topic_to_color[0], edgecolor='none', label="Topic 0"),
            Patch(facecolor=topic_to_color[1], edgecolor='none', label="Topic 1"),
            Patch(facecolor=topic_to_color[2], edgecolor='none', label="Topic 2"),
            Patch(facecolor=topic_to_color[3], edgecolor='none', label="Topic 3"),
            Patch(facecolor=topic_to_color[4], edgecolor='none', label="Topic 4"),
            Patch(facecolor=topic_to_color[5], edgecolor='none', label="Topic 5")
        ]
        plt.legend(
            handles=legend_handles,
            title="토픽 번호",
            bbox_to_anchor=(1.02, 1),
            loc='upper left',
            borderaxespad=0.3,
            fontsize=11,
            title_fontsize=12
        )

        # ─── 9. 제목 및 축 레이블 등 꾸미기 ─────────────────────────────────────────
        plt.title(
            "UMAP 2D 문서 임베딩과 BERTopic 토픽 분포",
            fontsize=20,
            pad=20
        )
        plt.xlabel("UMAP Dimension 1", fontsize=14)
        plt.ylabel("UMAP Dimension 2", fontsize=14)

        # 축 눈금 제거
        plt.xticks([])
        plt.yticks([])

        plt.tight_layout()

        # Jupyter Notebook(.ipynb) 환경에서는 plt.show() 한 줄만으로 인라인 렌더링됩니다.
        # plt.show()

        # ─── 10. 벡터 형식 저장 (기존 파일 덮어쓰기) ─────────────────────────────────────────
        import time
        umap_file = "umap2d_topics_custom_color_pret.png"
        
        # 파일이 이미 존재하면 건너뛰기
        if os.path.exists(umap_file):
            print(f"⏭️ UMAP 시각화 파일이 이미 존재합니다. 건너뜁니다: {umap_file}")
        else:
            print(f"📊 UMAP 시각화 파일을 새로 생성합니다: {umap_file}")
            plt.savefig(umap_file, dpi=300)
            
            # 파일이 제대로 생성되었는지 확인
            if os.path.exists(umap_file):
                file_size = os.path.getsize(umap_file)
                print(f"✅ UMAP 시각화 저장 완료: {umap_file} ({file_size} bytes)")
            else:
                print(f"❌ UMAP 시각화 파일 저장 실패: {umap_file}")
            
        plt.close()  # 메모리 정리
        # plt.savefig("umap2d_topics_custom_color_pret.svg", dpi=300)






        import os
        import matplotlib.font_manager as fm
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        import plotly.io as pio

        # ─── 0. Pretendard TTF 등록 (Matplotlib을 통해 폰트 이름 추출) ─────────────────────────
        font_path = "data/Pretendard-1.3.9/public/variable/PretendardVariable.ttf"
        if not os.path.exists(font_path):
            raise FileNotFoundError(f"Pretendard TTF 파일을 찾을 수 없습니다: {font_path}")

        # Matplotlib font_manager를 이용해 Pretendard를 등록한 뒤, 실제 폰트 이름을 가져옵니다.
        fm.fontManager.addfont(font_path)
        pret_name = fm.FontProperties(fname=font_path).get_name()
        # 이제 pret_name 변수에 예를 들어 "Pretendard Variable" 같은 정확한 폰트 패밀리 이름이 들어갑니다.

        # ─── 1. Plotly 기본 템플릿 및 한글 폰트 세팅 ─────────────────────────────────────────
        pio.templates.default = "simple_white"
        default_font = pret_name  # “AppleGothic” 대신 “Pretendard Variable”을 사용합니다.

        # ─── 2. BERTopic 모델 준비 ─────────────────────────────────────────────────────────
        # 이미 학습된 BERTopic 모델 객체(topic_model)가 메모리에 올라와 있어야 합니다.
        # 만약 파일에서 불러와야 한다면, 아래 두 줄의 주석을 해제하고 경로를 지정하세요:
        # from bertopic import BERTopic
        # topic_model = BERTopic.load("path/to/your_saved_model")

        # ─── 3. 토픽별 상위 12개 키워드(단어) 및 점수 추출 ──────────────────────────────────
        # 이 부분은 나중에 실제 토픽 모델이 생성된 후에 실행되도록 이동

        # ─── 4. 서브플롯(2행×3열) 생성 ────────────────────────────────────────────────────
        fig = make_subplots(
            rows=2, cols=3,
            subplot_titles=[
                "Topic 0: Top 10 words",
                "Topic 1: Top 10 words",
                "Topic 2: Top 10 words",
                "Topic 3: Top 10 words",
                "Topic 4: Top 10 words",
                "Topic 5: Top 10 words",
            ],
            # 1행과 2행 사이 간격을 충분히 두기 위해 vertical_spacing을 조정합니다.
            vertical_spacing=0.15,
            horizontal_spacing=0.08
        )

        # ─── 5. 토픽별 색상 (원하는 색으로 수정 가능) ────────────────────────────────────────
        colors = {
            0: "#8dd3c7",
            1: "#4eb3d3",
            2: "#08589e",
            3: "#fdb462",
            4: "#fb8072",
            5: "#b30000"
        }

        # 이 부분은 실제 토픽 모델 생성 후에 실행되도록 이동됨
        
        
        
        
        # Vectorizer 모델 설정
        vectorizer_model = CountVectorizer(vocabulary=list(vocab), ngram_range=(1, 1), min_df=2, token_pattern=r"(?u)\b\w[\w_]+\b")  # min_df ,max_df=0.5,

        # UMAP 모델 설정
        umap_model = umap.UMAP(n_neighbors=20, n_components=10, min_dist=0.01, metric='cosine', random_state=seed) # , spread=3.0)

        # HDBSCAN 모델 설정
        hdbscan_model = hdbscan.HDBSCAN(min_cluster_size=40, min_samples=2, metric='euclidean', cluster_selection_method='eom', prediction_data=True) #min_samples=2,

        # cTF-IDF 모델 설정
        ctfidf_model = ClassTfidfTransformer(bm25_weighting=True, reduce_frequent_words=False)   #bm25_weighting=True, reduce_frequent_words=True)

        from sentence_transformers import SentenceTransformer, util
        # 2) 한국어 특화 SBERT 로드
        # Hugging Face 429 에러 임시 해결책 - 다른 모델 사용
        try:
            embedding_model = SentenceTransformer("snunlp/KR-SBERT-V40K-klueNLI-augSTS")
        except Exception as e:
            print(f"KR-SBERT 모델 로드 실패, 대체 모델 사용: {e}")
            # 대체 모델 사용
            embedding_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
        # ===============================================
        # 그리드서치 실행 여부 설정
        # ===============================================
        USE_GRID_SEARCH = False  # True: 그리드서치 실행, False: 미리 설정된 파라미터 사용
        
        # 미리 설정된 최적 파라미터 (그리드서치 없이 바로 사용)
        PRESET_PARAMS = {
            "n_neighbors": 35,
            "n_components": 7, 
            "min_dist": 0.5,
            "min_cluster_size": 50
        }
        
        if USE_GRID_SEARCH:
            print("🔍 그리드서치를 실행합니다...")
            #def grid():
            # 환경 변수 및 시드 설정
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            seed = 42
            #print(f'len:{len(lemmatized_patents)}')
            # 문서 토큰화 준비
            texts = [doc.split() for doc in lemmatized_patents]
            dictionary = Dictionary(texts)

            #하이퍼파라미터 그리드 정의
            # param_grid = {
            #     "n_neighbors": [10, 15, 20, 30, 40, 50],
            #     "n_components": [5, 8, 10],
            #     "min_dist": [0, 0.01],
            #     "min_cluster_size": [15, 20, 25, 30, 40, 50]
            # }

            param_grid = {
                "n_neighbors": [35],
                "n_components": [7],
                "min_dist": [0.01],
                "min_cluster_size": [40]
            }
        else:
            print("⚡ 미리 설정된 파라미터로 바로 진행합니다...")
            print(f"   - n_neighbors: {PRESET_PARAMS['n_neighbors']}")
            print(f"   - n_components: {PRESET_PARAMS['n_components']}")
            print(f"   - min_dist: {PRESET_PARAMS['min_dist']}")
            print(f"   - min_cluster_size: {PRESET_PARAMS['min_cluster_size']}")
            
            # 그리드서치 없이 바로 BERTopic 모델 훈련으로 건너뛰기
            # UMAP 모델 설정 (미리 설정된 파라미터 사용)
            umap_model = umap.UMAP(
                n_neighbors=PRESET_PARAMS["n_neighbors"], 
                n_components=PRESET_PARAMS["n_components"], 
                min_dist=PRESET_PARAMS["min_dist"], 
                metric='cosine', 
                random_state=seed
            )
            
            # HDBSCAN 모델 설정 (미리 설정된 파라미터 사용)
            hdbscan_model = hdbscan.HDBSCAN(
                min_cluster_size=PRESET_PARAMS["min_cluster_size"], 
                min_samples=2, 
                metric='euclidean', 
                cluster_selection_method='eom', 
                prediction_data=True
            )
            
            # BERTopic 모델 초기화 및 훈련 (미리 설정된 파라미터 사용)
            topic_model = BERTopic(
                language="korean",
                calculate_probabilities=True,
                nr_topics='auto',
                top_n_words=15,
                vectorizer_model=vectorizer_model,
                embedding_model=embedding_model,
                umap_model=umap_model,
                hdbscan_model=hdbscan_model,
                ctfidf_model=ctfidf_model,
                verbose=True
            )
            
            # 주제 모델 훈련
            topics, probabilities = topic_model.fit_transform(lemmatized_patents)
            
            # 실제 토픽 모델 결과로 차트 데이터 생성
            top_n = 12
            topic_terms = {}
            topic_scores = {}
            
            all_topics = list(topic_model.get_topics().keys())
            print(f"🔍 전체 토픽 번호들: {all_topics}")
            
            # 실제 생성된 토픽들을 기반으로 차트 데이터 생성 (최대 6개로 제한)
            valid_topics = sorted([t for t in all_topics if t != -1])[:6]  # 최대 6개만 선택
            print(f"🔍 선택된 토픽들 (최대 6개): {valid_topics}")
            
            for topic_num in valid_topics:
                terms_scores = topic_model.get_topic(topic_num)  # [(term, score), ...]
                if terms_scores:
                    top_terms_scores = terms_scores[:top_n]
                    terms = [term for term, score in top_terms_scores]
                    scores = [score for term, score in top_terms_scores]
                    topic_terms[topic_num] = terms
                    topic_scores[topic_num] = scores
                    print(f"✅ Topic {topic_num}: {len(terms)}개 키워드 - {terms[:5]}...")
                else:
                    topic_terms[topic_num] = []
                    topic_scores[topic_num] = []
            
            # Chrome 의존성 문제 해결을 위해 matplotlib으로 차트 생성
            fig_mpl, axes = plt.subplots(2, 3, figsize=(15, 10))
            fig_mpl.suptitle('Topic 0~5: Top 10 words 분포', fontsize=20, y=0.98)
            
            colors_mpl = {
                0: "#8dd3c7", 1: "#4eb3d3", 2: "#08589e", 
                3: "#fdb462", 4: "#fb8072", 5: "#b30000"
            }
            
            # 선택된 토픽들에 맞춰 차트 생성 (최대 6개)
            for i, topic_num in enumerate(valid_topics):
                row = i // 3
                col = i % 3
                ax = axes[row, col]
                
                terms = topic_terms.get(topic_num, [])
                scores = topic_scores.get(topic_num, [])
                
                if terms:
                    # 내림차순으로 정렬 (높은 점수가 위쪽에)
                    y_pos = range(len(terms))
                    ax.barh(y_pos, scores[::-1], color=colors_mpl.get(i, "#cccccc"), alpha=0.8)
                    ax.set_yticks(y_pos)
                    ax.set_yticklabels(terms[::-1], fontsize=10)
                    ax.set_xlabel('c-TF-IDF', fontsize=12)
                    ax.set_title(f'Topic {topic_num}: Top 10 words', fontsize=14, pad=10)
                    ax.grid(axis='x', alpha=0.3)
                else:
                    ax.set_title(f'Topic {topic_num}: No data', fontsize=14, pad=10)
                    
            plt.tight_layout()
            
            # Topic words chart 파일 저장 (파일이 없을 때만 생성)
            chart_file = "topic_words_chart.png"
            
            # 파일이 이미 존재하면 건너뛰기
            if os.path.exists(chart_file):
                print(f"⏭️ 토픽 차트 파일이 이미 존재합니다. 건너뜁니다: {chart_file}")
            else:
                print(f"📈 토픽 차트 파일을 새로 생성합니다: {chart_file}")
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                
                # 파일이 제대로 생성되었는지 확인
                if os.path.exists(chart_file):
                    file_size = os.path.getsize(chart_file)
                    print(f"✅ 토픽 차트 저장 완료: {chart_file} ({file_size} bytes)")
                else:
                    print(f"❌ 토픽 차트 파일 저장 실패: {chart_file}")
                
            plt.close(fig_mpl)
            
            # 토픽 결과 처리 후 반환 (최대 6개로 제한)
            topics_dict = {}
            for topic_num in valid_topics:  # 이미 6개로 제한된 토픽들만 사용
                words = [word for word, _ in topic_model.get_topic(topic_num)]
                topics_dict[topic_num] = words

            print(f"🎯 최종 반환할 토픽 수: {len(topics_dict)}개 (최대 6개로 제한)")
            return topics_dict

            # ========== 그리드서치 코드 (주석처리됨) ==========
            # 총 조합 수 계산
            total_combinations = (
                len(param_grid["n_neighbors"]) *
                len(param_grid["n_components"]) *
                len(param_grid["min_dist"]) *
                len(param_grid["min_cluster_size"])
            )

            results = []

            # 결과를 저장할 파일 경로
            output_path = "../0601_grid_search_results1154.json"

            # (1) 빈 JSON 파일을 미리 생성해 두면, 이후 덮어쓰기가 편해집니다.
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump({"results": [], "best": None}, f, ensure_ascii=False, indent=4)

            # Grid search with progress bar
            for grid_idx, (n_neighbors, n_components, min_dist, min_cs) in enumerate(tqdm(
                    itertools.product(
                        param_grid["n_neighbors"],
                        param_grid["n_components"],
                        param_grid["min_dist"],
                        param_grid["min_cluster_size"]
                    ),
                    total=total_combinations,
                    desc="Grid Search"
            )):
                # grid 진행상황 저장
                progress = {
                    "stage": "grid",
                    "current": grid_idx + 1,
                    "total": total_combinations,
                    "message": f"Grid {grid_idx + 1}/{total_combinations} 조합 평가 중"
                }
                with open("progress.json", "w", encoding="utf-8") as f:
                    json.dump(progress, f, ensure_ascii=False)

                # 2.1) UMAP 모델 정의
                umap_model = UMAP(
                    n_neighbors=n_neighbors,
                    n_components=n_components,
                    min_dist=min_dist,
                    metric='cosine',
                    random_state=seed
                )
                # 2.2) HDBSCAN 모델 정의
                hdbscan_model = HDBSCAN(
                    min_cluster_size=min_cs,
                    min_samples=2,
                    metric='euclidean',
                    cluster_selection_method='eom',
                    prediction_data=True
                )

                # 2.3) BERTopic 학습
                topic_model = BERTopic(
                    language="korean",
                    calculate_probabilities=True,
                    nr_topics='auto',
                    top_n_words=15,
                    vectorizer_model=vectorizer_model,
                    embedding_model=embedding_model,
                    umap_model=umap_model,
                    hdbscan_model=hdbscan_model,
                    ctfidf_model=ctfidf_model,
                    verbose=False
                )
                try:
                    topics, probs = topic_model.fit_transform(lemmatized_patents)
                except Exception as e:
                    print("❌ fit_transform 중 에러 발생:", e)
                    return {}  # 빈 dict 반환
                #print('-------------test1-------------')

                topic_words = {
                    str(topic_id): [word for word, _ in topic_model.get_topic(topic_id)]
                    for topic_id in topic_model.get_topic_freq().Topic
                    if topic_id != -1
                }
                if len(topic_words) < 3:
                    continue

                # -------------------------------------------------------------
                # 4) Coherence 계산
                # -------------------------------------------------------------
                coherence_per_topic = {}
                for topic_id, words in topic_words.items():
                    cm = CoherenceModel(
                        topics=[words],
                        texts=texts,
                        dictionary=dictionary,
                        coherence='c_v'
                    )
                    coherence_per_topic[topic_id] = cm.get_coherence()
                mean_coh = sum(coherence_per_topic.values()) / len(coherence_per_topic)
                if mean_coh < 0.4:
                    continue
                #print('-------------test2-------------')
                # -------------------------------------------------------------
                # 5) 토픽 빈도(Count) 저장 (노이즈 포함)
                # -------------------------------------------------------------
                topic_freq_df = topic_model.get_topic_freq()
                topic_counts = {
                    str(int(row["Topic"])): int(row["Count"])
                    for _, row in topic_freq_df.iterrows()
                }

                # -------------------------------------------------------------
                # 6) 해당 조합 결과 생성
                # -------------------------------------------------------------
                current_result = {
                    "n_neighbors": n_neighbors,
                    "n_components": n_components,
                    "min_dist": min_dist,
                    "min_cluster_size": min_cs,
                    "coherence_per_topic": coherence_per_topic,
                    "mean_coherence": mean_coh,
                    "topic_counts": topic_counts,
                    "topic_words": topic_words
                }
                results.append(current_result)
                #print('-------------test3-------------')

                # -------------------------------------------------------------
                # 7) 현재까지의 results와 best를 JSON 파일에 실시간 덮어쓰기
                # -------------------------------------------------------------
                # 최적 조합을 계산하려면 지금까지의 results 중 가장 높은 mean_coherence를 찾습니다.
                best_so_far = max(results, key=lambda x: x["mean_coherence"])
                output_dict = {"results": results, "best": best_so_far}

                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(output_dict, f, ensure_ascii=False, indent=4)

            best = max(results, key=lambda x: x["mean_coherence"]) if results else None
            if best:
                print(
                    f"Grid search 완료. 최적 조합: "
                    f"{best['n_neighbors']}, {best['n_components']}, "
                    f"{best['min_dist']}, {best['min_cluster_size']} "
                    f"(평균 Coherence: {best['mean_coherence']:.4f})"
                )
            else:
                print("조건을 만족하는 결과가 없습니다.")

            # BERTopic 모델 초기화 및 훈련 (그리드서치 후)
            topic_model = BERTopic(
                language="korean",  # 언어 설정
                calculate_probabilities=True,  # 확률 계산 여부
                nr_topics='auto',  # 주제의 수 제한, auto로 해야 HDBSCAN 작동
                top_n_words=15,  # 각 주제의 상위 단어 수
                # 주제의 최소 크기
                vectorizer_model=vectorizer_model,  # 벡터화 모델
                embedding_model=embedding_model,  # 임베딩 모델
                umap_model=umap_model,  # UMAP 모델
                hdbscan_model=hdbscan_model,  # HDBSCAN 모델
                ctfidf_model=ctfidf_model,  # c-TFIDF 모델
                #representation_model=representation_model,
                verbose=True  # 진행 상황 출력 여부
            )

            # 주제 모델 훈련
            #print(f'check:{lemmatized_patents}')
            topics, probabilities = topic_model.fit_transform(lemmatized_patents)
            
            #-----------------GTM1-----------------
            #------------------------------------------------------------------
            
            # 토픽 번호를 가져오고 첫 번째 토픽(-1)을 제외
            topics_dict = {}
            all_topics = list(topic_model.get_topics().keys())
            print(f"🔍 전체 토픽 번호들: {all_topics}")
            
            # -1 토픽(노이즈) 제외하고 최대 6개 토픽만 포함
            valid_topics = sorted([t for t in all_topics if t != -1])[:6]  # 최대 6개로 제한
            print(f"🔍 선택된 토픽들 (최대 6개): {valid_topics}")
            
            for topic_num in valid_topics:
                words = [word for word, _ in topic_model.get_topic(topic_num)]
                topics_dict[topic_num] = words
                print(f"✅ Topic {topic_num}: {len(words)}개 키워드 - {words[:5]}...")

            print(f"🎯 최종 반환할 토픽 수: {len(topics_dict)}개 (최대 6개로 제한)")
            return topics_dict
#------------------------------------------------------------------------                       
    