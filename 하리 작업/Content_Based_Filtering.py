import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from itertools import chain

# 데이터 로드 함수
@st.cache_data
def load_data():
    # 파일 경로
    file_path = '/Users/hailey/Desktop/DS Project/KFT/KFT Dataset - Sheet1.csv'
    
    # 데이터 로드
    dataset = pd.read_csv(file_path)

    # Base Type 분리 및 고유값 추출
    dataset['Base Type'] = dataset['Base Type'].str.split(', ')  # 쉼표로 분리
    unique_base_types = sorted(set(chain.from_iterable(dataset['Base Type'].dropna())))  # 중복 제거 및 정렬

    # Combined Features 생성
    dataset['Combined Features'] = dataset['Flavor Tags'].fillna('') + ' ' + dataset['Base Type'].apply(
        lambda x: ' '.join(x) if isinstance(x, list) else ''
    )
    return dataset, unique_base_types

# 유사도 계산 함수
def get_recommendations(user_input, dataset):
    # TF-IDF 벡터화
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(dataset['Combined Features'])

    # 사용자 입력 벡터화
    user_vector = tfidf.transform([user_input])

    # 코사인 유사도 계산
    cosine_similarities = cosine_similarity(user_vector, tfidf_matrix)
    dataset['Similarity Score'] = cosine_similarities[0]

    # 상위 6개 음료 추천
    top_recommendations = dataset.sort_values(by='Similarity Score', ascending=False).head(6)
    return top_recommendations[['Menu', 'Category', 'Base Type', 'Flavor Tags', 'Similarity Score']]

# Streamlit 시작
st.title("Kung Fu Tea Recommendation System")

# 데이터 로드
dataset, base_type_options = load_data()

# 사용자 입력 옵션
st.header("Enter Your Preferences")

# 음료 카테고리 다중 선택
category_options = dataset['Category'].unique().tolist()
selected_categories = st.multiselect("Select Categories:", category_options)

# 베이스 타입 다중 선택 (중복 제거된 고유 옵션)
selected_base_types = st.multiselect("Select Base Types:", base_type_options)

# 맛 태그 체크박스 그룹
flavor_tag_options = sorted(list(set(chain.from_iterable(dataset['Flavor Tags'].dropna().str.split(', ')))))
selected_flavor_tags = st.multiselect("Select Flavor Tags:", flavor_tag_options)

# 추천 버튼
if st.button("Recommend"):
    # 사용자 입력 결합
    user_input = ' '.join(selected_flavor_tags)
    if selected_categories:
        user_input += ' ' + ' '.join(selected_categories)
    if selected_base_types:
        user_input += ' ' + ' '.join(selected_base_types)

    if user_input.strip():
        recommendations = get_recommendations(user_input, dataset)

        # 추천 결과 출력
        st.header("Recommended Drinks")
        st.write(recommendations)

        # 시각화 (막대 그래프)
        st.bar_chart(recommendations.set_index('Menu')['Similarity Score'])
    else:
        st.error("Please select at least one option.")

