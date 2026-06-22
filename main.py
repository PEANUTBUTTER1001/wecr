import pandas as pd
import streamlit as st

from crawling import crawling_saramin, crawling_work24, download_to_csv

st.set_page_config(page_title='채용 공고 크롤링 사이트')

st.title("🏢 사람인 채용공고 스크래퍼")
st.markdown("원하는 **지역, 직무, 기술스택**을 선택하여 사람인 채용공고를 검색하고 확인할 수 있습니다.")

site_select = st.radio("크롤링 사이트 선택", ['사람인', '고용24'])

with st.expander('🔽 상세 조건 검색'):
    col1, col2 = st.columns(2)

    with col1:
        search_text = st.text_input('검색어 입력', placeholder='예)ㅁㄴㅇㄹ')
        except_text = st.text_input('제외할 검색어 입력', placeholder='예)ㄹㅇㄴㅁ')
        select_pages = st.number_input('크롤링 페이지 수', step=1, min_value=1, max_value=100)

    with col2:
        if site_select == '사람인':
            # 지역
            loc_option = {
                    "전국": "",
                    "서울": "101000",
                    "경기": "102000",
                    "인천": "108000",
                    "부산": "106000",
                    "대구": "104000",
                    "광주": "105000",
                    "대전": "107000",
                    "울산": "111000",
                    "세종": "118000",
                    "강원": "109000",
                    "경남": "112000",
                    "경북": "113000",
                    "전남": "114000",
                    "전북": "115000",
                    "충남": "116000",
                    "충북": "117000",
                    "제주": "110000",
                    }
            selected_location = st.multiselect(
                    '지역을 선택하세요',
                    list(loc_option.keys()),
                    default=['전국'],
                    )

            locations = ",".join([loc_option[x] for x in selected_location if loc_option.get(x)])

            # 직무
            cat_options = {
                    "전체": None,
                    "IT개발·데이터": "2",
                    "경영·사무": "3",
                    "마케팅·홍보": "4",
                    "디자인": "9",
                    "영업": "5",
                    }

            selected_category = st.multiselect(
                    '직무 선택',
                    list(cat_options.keys()),
                    default=['IT개발·데이터'],
                    )

            category = ",".join([cat_options[x] for x in selected_category if cat_options.get(x)])

            # 경력
            career_options = {
                    '전체': '0', '신입': '1',
                    '경력': '2', '신입/경력': '3',
                    }

            selected_career = st.selectbox(
                    '경력 선택',
                    list(career_options.keys()),
                    )

            career = career_options[selected_career]

            # 학력
            edu_options = {
                    '전체': '0', '고졸': '1',
                    '대졸(2,3년)': '2', '대졸(4년)': '3',
                    '석사': '4', '박사': '5',
                    }

            selected_edu = st.selectbox('학력 선택', list(edu_options.keys()))

            edu = edu_options[selected_edu]

        else:
            # 지역
            region = st.text_input(
                    '지역 코드입력',
                    value='11000',
                    help='지역 코드 ....',
                    )

            # 직종
            occupation = st.text_input(
                    '직종 코드입력',
                    value='024',
                    help='직종 코드 제한',
                    )

            # 경력
            career_options = {
                    "전체": "A",
                    "신입": "N",
                    "경력": "E",
                    "관계없음": "Z",
                    }
            selected_career = st.selectbox(
                    '경력 입력',
                    list(career_options.keys()),
                    )
            career = career_options[selected_career]

            # 학력
            edu_options = {
                    "전체": "noEdu", "중졸이하": "01,02",
                    "고졸": "03", "대졸(2~3년)": "04",
                    "대졸(4년)": "05", "석사": "06",
                    "박사": "07", "학력무관": "00",
                    }
            selected_edu = st.selectbox(
                    '학력 선택',
                    list(edu_options.keys()),
                    )
            edu = edu_options[selected_edu]

crawling_clicked = st.button("조회", use_container_width=True, type='primary')


if 'df' not in st.session_state:
    st.session_state['df'] = pd.DataFrame()

if crawling_clicked:
    if not search_text:
        st.warning('검색어 입력')
    else:
        with st.spinner(f'{site_select}에서 {search_text} 검색 중...'):
            if site_select == '사람인':
                df = crawling_saramin(
                        search_text=search_text,
                        except_text=except_text,
                        region=locations,
                        category=category,
                        career=career,
                        education=edu,
                        max_pages=select_pages,
                        )

            else:
                df = crawling_work24(
                        search_text=search_text,
                        except_text=except_text,
                        region=region,
                        category=occupation,
                        career=career,
                        education=edu,
                        max_pages=select_pages,
                        )
        st.session_state['df'] = df

df = st.session_state['df']

if not df.empty:
    st.subheader('검색결과')
    st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            )

    csv_data = download_to_csv(df)

    st.download_button(
            label='csv', data=csv_data,
            file_name=f'crawling_result_{site_select}.csv',
            mime='text/csv',
            )
