from dotenv import load_dotenv
import os
from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from tabulate import tabulate  # pip install tabulate
import os
import openai
from dotenv import load_dotenv

class Step5:
    def last(self,x):
        load_dotenv()

        # OpenAI API 키 설정
        import os
        load_dotenv()
        openai_api_key = os.getenv('OPENAI_API_KEY')
        topic_words = x  # 여기서 x는 실제 값으로 변경

        # LLM 모델 선언
        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.5,
            openai_api_key=openai_api_key  # API 키 명시적 전달
        )

        # 프롬프트 템플릿
        system_prompt = (
            "너는 특허 기반 키워드를 분석하여, 기술적으로 타당하고 표현이 세련된 주제명을 생성하는 전문가야. "
            "각 키워드 묶음은 BerTopic으로 추출된 결과로, 해당 키워드들이 지닌 기술 흐름, 응용 가능성, 연관성 등을 종합적으로 고려해 "
            "기술 보고서, 정책 로드맵, 연구 과제명 등에 적합한 수준의 한 줄짜리 기술 제목을 생성해야 해. \n"
            "제목은 실제 기술명이나 연구과제명처럼 자연스럽고 직관적이어야 하며, 유망 기술의 방향성을 드러내야 해. "
            "설명은 생략하고, 결과는 다음 형식으로 출력해:\n\n"
            "제목: (기술 또는 연구 주제명)\n"
            "핵심 키워드: 키워드1, 키워드2, 키워드3, ..."
        )

        human_prompt_template = (
            "다음 키워드들을 바탕으로 관련성을 분석해, 기술 트렌드를 반영한 미래 유망 기술 또는 연구 주제명을 한 줄로 작성해줘.\n"
            "설명 없이, 아래 형식에 맞춰 출력해줘:\n\n"
            "제목: (기술 또는 연구 주제명)\n"
            "핵심 키워드: 키워드1, 키워드2, 키워드3, ..."
            "\n\n키워드 목록:\n{keywords}"
        )

        from langchain.prompts import ChatPromptTemplate
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", human_prompt_template),
        ])

        # 토픽명 생성 함수
        def generate_topic_names_llm(topic_words_dict):
            result_rows = []
            
            # 입력 검증
            if not topic_words_dict or not isinstance(topic_words_dict, dict):
                print("❌ 토픽 데이터가 비어있거나 올바르지 않습니다.")
                return []
                
            for topic_id, keywords in topic_words_dict.items():
                all_keywords_str = ", ".join(keywords)

                # LLM 호출
                chain = prompt_template | llm
                response = chain.invoke({"keywords": all_keywords_str})
                content = response.content.strip()

                # 응답 파싱
                topic_name = ""
                core_keywords_str = ""
                for line in content.splitlines():
                    if line.lower().startswith("제목:"):
                        topic_name = line.split(":", 1)[-1].strip()
                    elif "키워드" in line:
                        core_keywords_str = line.split(":", 1)[-1].strip()

                # 결과 행 저장
                result_rows.append([f"Topic {int(topic_id) + 1}", topic_name, core_keywords_str])
            return result_rows


        # 실행
        results = generate_topic_names_llm(topic_words)

        # 표 형태 출력
        headers = ["토픽 번호", "토픽", "내용"]
        print(tabulate(results, headers=headers, tablefmt="github"))

        # 보고서 생성 프롬프트 설정
        from langchain.prompts import ChatPromptTemplate

        report_prompt_template = ChatPromptTemplate.from_messages([
            ("system", "너는 첨단 기술 보고서를 작성하는 전문가야. 주제 제목과 핵심 키워드를 기반으로 기술 보고서 형식의 설명을 작성해."),
            ("human", "다음 정보를 바탕으로 기술 보고서 형식의 내용을 작성해줘.\n"
                      "형식: 개요, 기술 구성, 적용 분야, 개발 단계 (1~3차년도), 최종 목표, 활용 가능성 등으로 구성된 보고서\n\n"
                      "제목: {title}\n핵심 키워드: {keywords}")
        ])

        # 보고서 생성 및 저장
        import os
        os.makedirs("generated_reports", exist_ok=True)

        for topic_id, topic_name, keywords in results:
            # 1. 보고서 생성
            chain = report_prompt_template | llm
            response = chain.invoke({"title": topic_name, "keywords": keywords})
            report_text = response.content.strip()

            # 2. Markdown 파일로 저장
            filename = f"{topic_id.replace(' ', '_')}_{topic_name[:30]}.md"
            filepath = os.path.join("./generated_reports", filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"# {topic_name}\n")
                f.write(f"**핵심 키워드:** {keywords}\n\n")
                f.write(report_text)

            print(f"✅ 저장 완료: {filepath}")
