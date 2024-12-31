import streamlit as st
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from itertools import chain

# 데이터 로드 함수
@st.cache_data
def load_data():
    # 데이터 파일 경로
    dataset = pd.read_csv('KFT Dataset - Sheet1.csv')
    
    # Base Type 분리 및 중복 제거
    dataset['Base Type'] = dataset['Base Type'].str.split(', ')
    unique_base_types = sorted(set(chain.from_iterable(dataset['Base Type'].dropna())))
    
    # Combined Features 생성
    dataset['Combined Features'] = dataset['Flavor Tags'].fillna('') + ' ' + dataset['Base Type'].apply(
        lambda x: ' '.join(x) if isinstance(x, list) else ''
    )
    return dataset, unique_base_types

# KNN 모델 생성 함수
@st.cache_data
def create_knn_model(dataset):
    # TF-IDF 벡터화
    tfidf = TfidfVectorizer(stop_words='english')
    tfidf_matrix = tfidf.fit_transform(dataset['Combined Features'])

    # KNN 모델 생성
    knn = NearestNeighbors(n_neighbors=6, metric='cosine')
    knn.fit(tfidf_matrix)
    return knn, tfidf

# 추천 함수
def get_recommendations(user_input, dataset, knn, tfidf):
    # 사용자 입력 벡터화
    user_vector = tfidf.transform([user_input])

    # KNN 모델을 사용해 추천
    distances, indices = knn.kneighbors(user_vector)

    # 추천된 음료 가져오기
    recommended_drinks = dataset.iloc[indices[0]][['Menu', 'Category', 'Base Type', 'Flavor Tags']]
    return recommended_drinks

# Streamlit UI
st.title("Kung Fu Tea Recommendation System (KNN)")

# 데이터 로드
dataset, base_type_options = load_data()

# KNN 모델 생성
knn, tfidf = create_knn_model(dataset)

# 사용자 입력 UI
st.header("Enter Your Preferences")

# 음료 카테고리 다중 선택
category_options = dataset['Category'].unique().tolist()
selected_categories = st.multiselect("Select Categories:", category_options)

# 베이스 타입 다중 선택 (중복 제거된 고유 옵션)
selected_base_types = st.multiselect("Select Base Types:", base_type_options)

# 맛 태그 다중 선택
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
        recommendations = get_recommendations(user_input, dataset, knn, tfidf)

        # 추천 결과 출력
        st.header("Recommended Drinks")
        st.write(recommendations)
    else:
        st.error("Please select at least one option.")



