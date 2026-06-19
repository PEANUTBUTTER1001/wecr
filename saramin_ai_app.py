import streamlit as st
import pandas as pd
from saramin_ai_crawler import fetch_ai_developer_jobs

st.set_page_config(page_title="AI 개발자 채용공고 상세 분석기", page_icon="🤖", layout="wide")

st.title("🤖 AI 개발자 채용공고 상세 분석기")
st.markdown("사람인에서 'AI 개발자' 채용공고를 검색하고, 상세 요강의 **주요업무**, **자격요건**, **우대사항**을 자동으로 분석하여 보여줍니다.")

with st.sidebar:
    st.header("🔍 검색 설정")
    search_keyword = st.text_input("검색어", value="AI 개발자")
    pages = st.number_input("수집할 페이지 수 (페이지당 약 40건)", min_value=1, max_value=10, value=1)
    
    st.divider()
    search_button = st.button("🚀 데이터 수집 및 분석 시작", use_container_width=True)

if search_button:
    if not search_keyword.strip():
        st.warning("검색어를 입력해주세요.")
    else:
        st.info(f"🔎 검색어: **{search_keyword}** | 수집 페이지: **{pages}** 페이지")
        
        with st.spinner('상세 요강을 수집하고 분석하는 중입니다. 상세 페이지를 하나씩 방문하므로 시간이 다소 소요될 수 있습니다...'):
            try:
                # 데이터 수집
                scraped_jobs = fetch_ai_developer_jobs(searchword=search_keyword, max_pages=pages, items_per_page=40)
                
                if not scraped_jobs:
                    st.warning("조건에 맞는 채용공고가 없거나 수집에 실패했습니다.")
                else:
                    st.success(f"총 {len(scraped_jobs)}개의 채용공고를 성공적으로 분석했습니다!")
                    
                    df = pd.DataFrame(scraped_jobs)
                    
                    # DataFrame 출력 (링크 클릭 및 텍스트 래핑이 잘 되도록 설정)
                    st.dataframe(
                        df,
                        column_config={
                            "링크": st.column_config.LinkColumn("공고 링크", display_text="상세보기"),
                            "주요업무": st.column_config.TextColumn("주요업무", width="medium"),
                            "자격요건": st.column_config.TextColumn("자격요건", width="medium"),
                            "우대사항": st.column_config.TextColumn("우대사항", width="medium"),
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # CSV 다운로드 기능
                    csv_data = df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
                    st.download_button(
                        label="📥 분석 결과 CSV 다운로드",
                        data=csv_data,
                        file_name=f'ai_developer_jobs_analyzed.csv',
                        mime='text/csv',
                    )
            except Exception as e:
                st.error(f"데이터 수집 중 오류가 발생했습니다: {e}")
else:
    st.info("👈 왼쪽 사이드바에서 검색 조건을 설정하고 '데이터 수집 및 분석 시작' 버튼을 눌러주세요.")
