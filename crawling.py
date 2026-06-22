import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from io import StringIO

headers = {
        "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
        }


def crawling_saramin(
        search_text: str = "",
        except_text: str = None,
        region: str = None,
        category: str = None,
        career: str = '',
        education: str = '',
        max_pages: int = 1,
        ):
    url = "https://www.saramin.co.kr/zf_user/search"
    rows = []
    for page in range(1, max_pages + 1):

        params1 = {'searchword': search_text, 'except_read': except_text, 'comp_page': page}
        # 직무
        if category:
            params1['cat_mcd'] = category
        # 위치
        if region:
            params1['loc_mcd'] = region
        # 경력
        if career:
            params1['career_cd'] = career
        # 학력
        if education:
            params1['edu_cd'] = education
            

        try:
            request = requests.get(url, headers=headers, params=params1, timeout=10)

            columns = ['이름', '위치', '조건1', '조건2', '회사이름', '링크']

            soup = BeautifulSoup(request.text, 'html.parser')

            items = soup.select('div.item_recruit')

            for item in items:
                job_area = item.select_one('div.area_job')
                corp_area = item.select_one('div.area_corp')

                if not job_area:
                    continue

                job_title = job_area.select_one('.job_tit').get_text(strip=True)
                condition_area = job_area.select_one('.job_condition')
                spans = condition_area.select('span')

                location = spans[0].get_text(strip=True)
                condition1 = spans[1].get_text(strip=True)

                job_sector = item.select_one('div.job_sector')
                condition2 = job_sector.get_text(strip=True)

                # job_sector = item.find('div', class_='job_sector')

                cor_name_tag = corp_area.select_one('strong.corp_name span')
                if not cor_name_tag:
                    cor_name_tag = corp_area.select_one('strong.corp_name')
                cor_name = cor_name_tag.get_text(strip=True)

                link = job_area.select_one('.job_tit a')
                real_link = "https://www.saramin.co.kr" + link.get('href')

                rows.append(
                        {
                                '이름': job_title,
                                '위치': location,
                                '조건1': condition1,
                                '조건2': condition2,
                                '회사이름': cor_name,
                                '링크': real_link,
                                },
                        )
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
            break
    df = pd.DataFrame(rows)
    return df


def crawling_work24(
        search_text: str = "",
        except_text: str = None,
        region: str = None,
        category: str = None,
        career: str = '',
        education: str = '',
        max_pages: int = 1,
        ):

    url = "https://www.work24.go.kr/wk/a/b/1200/retriveDtlEmpSrchList.do"
    rows = []
    for page in range(1, max_pages + 1):

        params2 = {
                'srcKeyword': search_text,
                'notSrcKeyword': except_text,
                'pageIndex': page,
                'resultCnt': 10,
                'CodeDepth1Info': region,
                'occupation': '024',
                'careerTypes': "",
                'academicGbnoEdu': "",
                }
        try:
            request = requests.get(
                    url,
                    headers=headers,
                    params=params2,
                    timeout=10,
                    )

            soup = BeautifulSoup(request.text, 'html.parser')

            items = soup.select('table.box_table.type_pd24')

            for item in items:
                title = item.select_one('td.al_left.pd24').select('div.cell')[1]
                title_tag = title.select_one('a.t3_sb').get_text(strip=True)
                corp_name = item.select_one('a.cp_name').get_text(strip=True)
                location = item.select_one('li.site').select('p')[0].get_text(strip=True)
                career_edu = item.select_one(
                        'li.member',
                        )
                spans = career_edu.select('span.item.sm')
                career = spans[0].get_text(strip=True)
                edu = spans[1].get_text(strip=True)

                money = item.select_one('span.item.b1_sb').get_text(strip=True)
                money = re.sub(r'\s+', '', money)

                link_tag = item.select_one('div.box_table_group.gap_box08.column').select('div.cell')[1].select_one('a')
                link = "https://www.work24.go.kr" + link_tag.get('href')
                rows.append(
                        {
                                '이름': title_tag,
                                '위치': location,
                                '회사이름': corp_name,
                                '경력': career,
                                '학력': edu,
                                '링크': link,
                                },
                        )
        except Exception as e:
            print(f"오류가 발생했습니다: {e}")
            break

    df = pd.DataFrame(rows)
    return df


def download_to_csv(df):
    buffer = StringIO()
    df.to_csv(buffer, index=False)
    return buffer.getvalue().encode('utf-8-sig')


if __name__ == '__main__':
    # crawling_saramin("빅데이터")
    crawling_work24("빅데이터")
