from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from main import generate_report
from fastapi.responses import JSONResponse
import os
import json
import glob
from datetime import datetime
import asyncio
import markdown

app = FastAPI()

# CORS 허용 (모든 도메인에서 접근 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class KeywordRequest(BaseModel):
    keyword: str

@app.post("/generate_report")
async def generate_report_api(req: KeywordRequest):
    try:
        # 비동기로 실행하여 타임아웃 방지
        loop = asyncio.get_event_loop()
        markdown_report = await loop.run_in_executor(None, generate_report, req.keyword)
        
        # 마크다운을 HTML로 변환
        html_report = markdown.markdown(
            markdown_report,
            extensions=['tables', 'fenced_code', 'toc']
        )
        
        return {
            "markdown_report": markdown_report,
            "html_report": html_report
        }
    except Exception as e:
        print(f"보고서 생성 중 오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"보고서 생성 중 오류가 발생했습니다: {str(e)}")

@app.get("/progress")
def get_progress():
    if os.path.exists("progress.json"):
        with open("progress.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    else:
        return JSONResponse(content={"stage": "대기 중", "current": 0, "total": 1, "message": "진행 대기 중"})

@app.get("/list_reports")
def list_reports():
    """저장된 보고서 목록을 반환합니다."""
    reports_dir = "generated_reports"
    if not os.path.exists(reports_dir):
        return JSONResponse(content={"reports": []})
    
    report_files = glob.glob(os.path.join(reports_dir, "*.md"))
    reports = []
    
    for file_path in report_files:
        filename = os.path.basename(file_path)
        # 파일 생성 시간 가져오기
        creation_time = os.path.getctime(file_path)
        creation_date = datetime.fromtimestamp(creation_time).strftime("%Y-%m-%d %H:%M:%S")
        
        # 파일에서 제목 추출 (첫 번째 줄의 # 제목)
        title = filename.replace(".md", "")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                first_line = f.readline().strip()
                if first_line.startswith("# "):
                    title = first_line[2:].strip()
        except:
            pass
        
        reports.append({
            "filename": filename,
            "title": title,
            "created_at": creation_date
        })
    
    # 생성 시간 기준으로 최신순 정렬
    reports.sort(key=lambda x: x["created_at"], reverse=True)
    
    return JSONResponse(content={"reports": reports})

@app.get("/get_report/{filename}")
def get_report(filename: str):
    """특정 보고서의 내용을 반환합니다."""
    reports_dir = "generated_reports"
    file_path = os.path.join(reports_dir, filename)
    
    if not os.path.exists(file_path) or not filename.endswith(".md"):
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
        
        # 마크다운을 HTML로 변환
        html_content = markdown.markdown(
            markdown_content,
            extensions=['tables', 'fenced_code', 'toc']
        )
        
        return JSONResponse(content={
            "filename": filename,
            "markdown_content": markdown_content,  # 원본 마크다운도 제공
            "html_content": html_content  # HTML 변환된 내용
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서를 읽는 중 오류가 발생했습니다: {str(e)}")

@app.delete("/delete_report/{filename}")
def delete_report(filename: str):
    """특정 보고서를 삭제합니다."""
    reports_dir = "generated_reports"
    file_path = os.path.join(reports_dir, filename)
    
    if not os.path.exists(file_path) or not filename.endswith(".md"):
        raise HTTPException(status_code=404, detail="보고서를 찾을 수 없습니다.")
    
    try:
        os.remove(file_path)
        return JSONResponse(content={
            "message": f"보고서 '{filename}'이 성공적으로 삭제되었습니다.",
            "deleted_file": filename
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"보고서를 삭제하는 중 오류가 발생했습니다: {str(e)}") 