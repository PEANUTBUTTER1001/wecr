import csv
import time
import requests
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup, Tag

# --- 상수 정의 (Constants) ---
SARAMIN_SEARCH_URL = "https://www.saramin.co.kr/zf_user/search"
SARAMIN_DETAIL_API_URL = "https://www.saramin.co.kr/zf_user/jobs/relay/view-detail"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def extract_text(tag: Optional[Tag]) -> str:
    return tag.text.strip() if tag else "N/A"

def extract_section(text: str, start_keywords: List[str], end_keywords: List[str]) -> str:
    """텍스트에서 특정 시작 키워드부터 끝 키워드 전까지의 내용을 추출합니다."""
    start_idx = -1
    for k in start_keywords:
        idx = text.find(k)
        if idx != -1:
            start_idx = idx + len(k)
            break
            
    if start_idx == -1: return 'N/A'
    
    end_idx = len(text)
    for k in end_keywords:
        idx = text.find(k, start_idx)
        if idx != -1 and idx < end_idx:
            end_idx = idx
            
    # 정제된 텍스트 반환 (연속된 공백 제거 및 양쪽 공백 제거)
    result = text[start_idx:end_idx].strip()
    result = re.sub(r'\s+', ' ', result)
    return result

def get_job_details(rec_idx: str) -> Dict[str, str]:
    """공고 상세 페이지(iframe/API)에서 텍스트를 추출하여 주요업무, 자격요건, 우대사항을 파싱합니다."""
    try:
        res = requests.get(f"{SARAMIN_DETAIL_API_URL}?rec_idx={rec_idx}", headers=HEADERS)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 텍스트 추출 (줄바꿈을 공백으로 치환)
        text = soup.get_text(separator=' ').strip()
        
        # 상세 내용이 거의 없고 이미지 태그가 많다면 이미지 채용공고일 확률이 높음
        if len(text) < 100 and soup.find('img'):
            return {
                '주요업무': '상세 이미지 참고',
                '자격요건': '상세 이미지 참고',
                '우대사항': '상세 이미지 참고'
            }

        main_work = extract_section(
            text, 
            ['주요업무', '주요 업무', '담당업무', '담당 업무', '포지션 상세'], 
            ['자격요건', '자격 요건', '우대사항', '우대 사항', '혜택 및 복지', '근무환경', '전형절차']
        )
        
        qualifications = extract_section(
            text, 
            ['자격요건', '자격 요건', '지원자격', '지원 자격'], 
            ['우대사항', '우대 사항', '혜택 및 복지', '근무환경', '전형절차']
        )
        
        preferences = extract_section(
            text, 
            ['우대사항', '우대 사항'], 
            ['혜택 및 복지', '근무환경', '전형절차', '유의사항', '복리후생']
        )
        
        return {
            '주요업무': main_work,
            '자격요건': qualifications,
            '우대사항': preferences
        }
        
    except Exception as e:
        print(f"상세 정보 수집 중 오류 발생 (rec_idx: {rec_idx}): {e}")
        return {
            '주요업무': 'Error',
            '자격요건': 'Error',
            '우대사항': 'Error'
        }

def parse_job_item(item: Tag) -> Dict[str, str]:
    """단일 채용 공고 HTML 요소에서 필요한 데이터를 추출합니다."""
    # 1. 회사명
    corp_name = extract_text(item.find('strong', class_='corp_name'))
    
    # 2. 공고 제목 및 링크
    title, link = "N/A", "N/A"
    rec_idx = None
    job_tit_tag = item.find('h2', class_='job_tit')
    if job_tit_tag and job_tit_tag.find('a'):
        a_tag = job_tit_tag.find('a')
        title = a_tag.get('title', a_tag.text.strip())
        href = a_tag['href']
        link = "https://www.saramin.co.kr" + href
        
        # URL에서 rec_idx 추출
        match = re.search(r'rec_idx=(\d+)', href)
        if match:
            rec_idx = match.group(1)
            
    # 3. 근무 조건
    condition_tag = item.find('div', class_='job_condition')
    conditions_text = ', '.join([span.text.strip() for span in condition_tag.find_all('span')]) if condition_tag else "N/A"
        
    # 4. 기술 스택 및 직무 분야
    sector_tag = item.find('div', class_='job_sector')
    if sector_tag:
        for span in sector_tag.find_all('span', class_='job_day'):
            span.decompose()
        sectors_text = ' '.join(sector_tag.text.strip().split())
    else:
        sectors_text = "N/A"
        
    # 5. 마감일
    date_tag = item.find('div', class_='job_date')
    deadline = extract_text(date_tag.find('span', class_='date') if date_tag else None)
    
    job_data = {
        '회사명': corp_name,
        '공고제목': title,
        '링크': link,
        '근무조건': conditions_text,
        '기술스택_분야': sectors_text,
        '마감일': deadline
    }
    
    # 상세 페이지 내용 파싱 (주요업무, 자격요건, 우대사항)
    if rec_idx:
        details = get_job_details(rec_idx)
        job_data.update(details)
    else:
        job_data.update({'주요업무': 'N/A', '자격요건': 'N/A', '우대사항': 'N/A'})
        
    return job_data

def fetch_ai_developer_jobs(searchword: str = 'ai 개발자', items_per_page: int = 20, max_pages: int = 1) -> List[Dict[str, str]]:
    """AI 개발자 채용공고를 스크래핑합니다. (테스트를 위해 기본 1페이지 수집)"""
    params = {
        'searchword': searchword,
        'recruitPage': 1,
        'recruitSort': 'relation',
        'recruitPageCount': items_per_page
    }
    
    all_jobs = []
    print(f"'{searchword}' 채용공고 스크래핑을 시작합니다...")
    
    while params['recruitPage'] <= max_pages:
        print(f"[{params['recruitPage']} 페이지] 수집 중...")
        
        try:
            response = requests.get(SARAMIN_SEARCH_URL, params=params, headers=HEADERS)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"네트워크 오류 발생: {e}")
            break
            
        soup = BeautifulSoup(response.text, 'html.parser')
        job_items = soup.find_all('div', class_='item_recruit')
        
        if not job_items:
            break
            
        for item in job_items:
            job_data = parse_job_item(item)
            all_jobs.append(job_data)
            
        if len(job_items) < items_per_page:
            break
            
        params['recruitPage'] += 1
        time.sleep(1)
        
    return all_jobs

def save_to_csv(jobs: List[Dict[str, str]], filename: str) -> None:
    if not jobs:
        print("\n수집된 공고가 없어 파일을 생성하지 않습니다.")
        return
        
    try:
        with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
            writer.writeheader()
            writer.writerows(jobs)
        print(f"\n성공적으로 완료되었습니다! 총 {len(jobs)}개의 공고 -> '{filename}'")
    except IOError as e:
        print(f"\n파일 저장 중 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    scraped_jobs = fetch_ai_developer_jobs(searchword='ai 개발자', items_per_page=20, max_pages=1)
    save_to_csv(scraped_jobs, filename='saramin_ai_developer.csv')
