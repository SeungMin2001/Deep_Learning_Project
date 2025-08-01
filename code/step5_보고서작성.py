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
        # 🌐 LLM 선언
        llm = ChatOpenAI(model="gpt-4o", temperature=0.5)

        # 🧾 기술 보고서 작성 프롬프트
        report_prompt_template = ChatPromptTemplate.from_messages([
            ("system",
            "너는 첨단 기술 보고서를 작성하는 전문가이자 기술 전략 컨설턴트야. "
            "다음 주제 제목과 키워드를 기반으로 기업이 실제로 사업화 전략을 세울 수 있도록 기술 보고서를 작성해줘. "
            "보고서 내용에 다시 주제 제목을 명시할 필요는 없어.\n\n"

            "**각 항목은 반드시 '항목명:' 형식으로 시작해.**\n"
            "예: '개요: ...'\n\n"

            "📌 작성 규칙:\n"
            "- 각 항목은 단순 설명이 아니라 기업이 실질적으로 활용 가능한 전략을 포함해야 해.\n"
            "- '기술 구성', '적용 분야', '개발 단계별 목표', '관련 기술 보유 기업 및 제조사 현황' 항목에서는 **각 세부 기술 또는 사례마다 대표 키워드를 번호없이 괄호로 제시한 후 설명하는 방식**으로 작성해줘.\n"
            "  예: (주행 기술) 실내 환경 맵핑과 자율 경로 설정 기술을 통해...\n"
            "- 기술 구성 항목에서는 핵심 기술별 차별화 포인트 및 구현 방안을 제시해.\n"
            "- 적용 분야에서는 수요가 있는 산업 및 시장을 구체적으로 제시하고, 시장 규모나 성장 가능성을 간단히 언급해.\n"
            "- 개발 단계별 목표는 (1차년도), (2차년도), (3차년도) 까지만 제시하고, 연차별 R&D 전략과 실증 또는 제품화 수준을 고려해서 작성해.\n"
            "- 활용 가능성은 기술의 파급력, 확장 가능성, 타 기술과의 융합 가능성을 제안 형태로 서술해.\n"
            "- 관련 기술 보유 기업 및 제조사 현황은 주요 기업별 기술 특징, 차별화 포인트, 벤치마킹 요소를 중심으로 작성해.\n\n"

            "📄 필수 항목:\n"
            "- 개요\n"
            "- 기술 구성\n"
            "- 적용 분야\n"
            "- 개발 단계별 목표\n"
            "- 최종 목표\n"
            "- 활용 가능성\n"
            "- 관련 기술 보유 기업 및 제조사 현황\n\n"

            "보고서는 기업 실무자, 투자자 또는 기술 기획자가 바로 참고할 수 있을 정도로 "
            "**명확하고 전략적이며, 전문적인 문장**으로 구성해줘. "
            "기술 소개가 아니라, 기술 기반 사업 전략 보고서라는 점을 꼭 기억해줘."
            ),

            ("human",
            "다음 정보를 바탕으로 기술 보고서를 작성해줘.\n\n"
            "제목: {title}\n"
            "핵심 키워드: {keywords}")
        ])

        # 📚 섹션 제목 후보 리스트
        SECTION_TITLES = [
            "개요", "기술 구성", "적용 분야",
            "개발 단계별 목표", "최종 목표",
            "활용 가능성", "관련 기술 보유 기업 및 제조사 현황"
        ]

        # 🧹 응답 정리 및 마크다운 Bold 처리
        def clean_and_format_report(report_text):
            paragraphs = []
            current_section = None
            content_accumulator = []

            lines = report_text.strip().split("\n")
            for line in lines:
                line = line.strip()
                if not line:
                    continue

                is_section = False
                for title in SECTION_TITLES:
                    if re.match(fr"^(#+\s*)?\d*[\.\)]?\s*{title}[:：]?$", line, re.IGNORECASE):
                        if current_section:
                            paragraphs.append((current_section, "\n".join(content_accumulator).strip()))
                            content_accumulator = []
                        current_section = title
                        is_section = True
                        break

                if not is_section:
                    content_accumulator.append(line)

            if current_section:
                paragraphs.append((current_section, "\n".join(content_accumulator).strip()))

            return paragraphs

        # 🧾 마크다운 Bold 처리 함수 (텍스트 내 **부분 Bold 처리)
        def add_markdown_paragraph(doc, text):
            p = doc.add_paragraph()

            # 1️⃣ "- 키워드:" 형태를 모두 "(**키워드**)" 로 변경
            text = re.sub(r"^- ([^:]+?)\s*:\s*", r"(\1) ", text)

            # 2️⃣ 마크다운 굵은 텍스트 처리 (**텍스트**)
            pattern = r"(\(\*\*.+?\*\*\))"
            pos = 0
            for match in re.finditer(pattern, text):
                if match.start() > pos:
                    p.add_run(text[pos:match.start()]).font.size = Pt(11)

                bold_text = match.group(2)
                run = p.add_run(bold_text)
                run.bold = True
                run.font.size = Pt(11)
                pos = match.end()

            if pos < len(text):
                p.add_run(text[pos:]).font.size = Pt(11)

            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


        # 📤 Word 저장 함수
        def save_report_as_docx(title, keywords, report_text, filename):
            doc = Document()

            # 제목
            doc.add_heading(title, level=1)

            # 키워드
            p_kw = doc.add_paragraph()
            run_kw = p_kw.add_run(f"핵심 키워드: {keywords}")
            run_kw.bold = True
            run_kw.font.size = Pt(11)

            # 본문 구성
            cleaned_sections = clean_and_format_report(report_text)
            for section_title, content in cleaned_sections:
                # 섹션 제목
                p_title = doc.add_paragraph()
                run_title = p_title.add_run(section_title)
                run_title.bold = True
                run_title.font.size = Pt(13)

                # 섹션 내용
                for paragraph in content.split('\n'):
                    paragraph = paragraph.strip()
                    if paragraph:
                        add_markdown_paragraph(doc, paragraph)

            os.makedirs("reports_docx.v8", exist_ok=True)
            filepath = os.path.join("reports_docx.v8", filename)
            doc.save(filepath)
            print(f"✅ 저장 완료: {filepath}")

        # 🔁 실행 함수
        def generate_reports_from_results(topic_result_list):
            for i, (topic_number, title, keywords) in enumerate(topic_result_list):
                print(f"\n🚀 생성 중: {title}")
                report_chain = report_prompt_template | llm
                response = report_chain.invoke({"title": title, "keywords": keywords})

                report_text = (
                    response.strip()
                    if isinstance(response, str)
                    else response.content.strip()
                )

                filename = f"{i}_{title[:30].replace(' ', '_')}.docx"
                save_report_as_docx(title, keywords, report_text, filename)

        # ✅ 사용 예시
        generate_reports_from_results(results)
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
