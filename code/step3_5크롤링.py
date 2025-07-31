import requests
import xml.etree.ElementTree as ET
import pandas as pd
import ast
import sqlite3
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

class Step2:
    def cra(self,x):

        query=x
        KEYWORDS = ast.literal_eval(query)
        # ------------------ 설정 ------------------
        #API_KEY = os.getenv('KIPRIS_API_KEY', 'FlDibi21AbaJM8ifjFmXv5OUEuAMpjJYqq6/HGOpye0=')  # 환경변수에서 읽기
        load_dotenv()
        API_KEY=os.getenv('KIPRIS_API_KEY')

        # 제외할 특허 상태
        EXCLUDE_STATUSES = ['거절', '무효', '소멸', '포기', '불수리', '심사청구취하']

        column_name_map = {
            'applicationNumber': '출원번호',
            'inventionTitle': '발명명칭',
            'applicantName': '출원인',
            'registerStatus': '등록상태',
            'applicationDate': '출원일',
            'registerDate': '등록일',
            'publicationDate': '공개일',
            'ipcNumber': 'IPC분류',
            'inventorName': '발명자',
            'abstract': '요약',
            "claim": "청구항",  # ← 추가
            "claimStatement": "청구항",  # ← 추가 가능
            "claimText": "청구항"
        }


        MAX_RESULTS = 60 # 전체 긁어오는 특허수 조절변수
        MAX_PAGES=10
        url = 'http://plus.kipris.or.kr/kipo-api/kipi/patUtiModInfoSearchSevice/getWordSearch'
        
        # ----------------------------------------------------------------------------------

        all_patents = []
        print(f"STEP1 에서 만든 검색식: {KEYWORDS}\n")
        # 🔍 키워드별 검색
        for keyword in KEYWORDS:
            print(f"\n🔍 키워드 '{keyword}' 검색 중...")

            
            for page in range(1,MAX_PAGES+1):
                #print('test')
                params = {
                    'word': keyword,
                    'year': '0',
                    'ServiceKey': API_KEY,
                    'numOfRows': 7   # 키워드 하나당 긁어오는 특허수 조절하는곳
                    #'page':page
                }

                response = requests.get(url, params=params)
                if response.status_code != 200:
                    print(f"요청 실패: {response.status_code}")
                    continue

                try:
                    root = ET.fromstring(response.content)
                    items = root.findall('.//item')
                    #print(f"{len(items)}건 수집됨.")

                    for item in items:
                        patent_data = {}
                        for elem in item:
                            tag = elem.tag
                            text = elem.text.strip() if elem.text else ''
                            label = column_name_map.get(tag, tag)
                            patent_data[label] = text

                        status = patent_data.get('registerStatus', '')
                        if status in EXCLUDE_STATUSES:
                            continue  # 건너뛰기

                        patent_data['검색 키워드'] = keyword
                        all_patents.append(patent_data)

                        # 진행상황 저장
                        progress = {
                            "stage": "특허 수집",
                            "current": len(all_patents),
                            "total": MAX_RESULTS,
                            "message": f"특허 {len(all_patents)}/{MAX_RESULTS}개 수집 중"
                        }
                        with open("progress.json", "w", encoding="utf-8") as f:
                            json.dump(progress, f, ensure_ascii=False)

                        if len(all_patents) >= MAX_RESULTS:
                            break

                except ET.ParseError as e:
                    print(f" XML 파싱 실패: {e}")
                    continue

                if len(all_patents) >= MAX_RESULTS:
                    break

            if len(all_patents) >= MAX_RESULTS:
                break

        print(f"\n 최종 수집 특허 수: {len(all_patents)}건")
        # 마지막 진행상황 저장 (완료)
        progress = {
            "stage": "특허 수집 완료",
            "current": len(all_patents),
            "total": MAX_RESULTS,
            "message": f"특허 수집 완료: {len(all_patents)}개"
        }
        with open("progress.json", "w", encoding="utf-8") as f:
            json.dump(progress, f, ensure_ascii=False)
        df = pd.DataFrame(all_patents)
        #print(df)

        #df.to_csv("/Users/shinseungmin/Documents/벌토픽_전체코드/code/extract.csv")
        df.to_csv('./extract.csv')