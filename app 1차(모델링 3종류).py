import streamlit as st
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

def load_data():
    dataset = pd.read_csv('KFT Dataset.csv')
    dataset['Flavor Tags'] = dataset['Flavor Tags'].fillna('').apply(lambda x: ', '.join(set(x.split(', '))))
    return dataset

# Initialize session state for selected tags
if "selected_tags" not in st.session_state:
    st.session_state["selected_tags"] = []

# Function to toggle tag selection
def toggle_tag(tag):
    """Toggle the selection of a flavor tag."""
    if tag in st.session_state["selected_tags"]:
        st.session_state["selected_tags"].remove(tag)
    else:
        st.session_state["selected_tags"].append(tag)


def display_tags_in_grid(tags, cols=5):
    """Display flavor tags as a grid with a visual state for selection."""
    rows = len(tags) // cols + (1 if len(tags) % cols != 0 else 0)
    tag_index = 0
    for row in range(rows):
        cols_container = st.columns(cols)
        for col in range(cols):
            if tag_index < len(tags):
                tag = tags[tag_index]
                # Use different styles for selected and unselected tags
                if tag in st.session_state["selected_tags"]:
                    cols_container[col].button(
                        tag,
                        key=f"selected_{tag}",
                        on_click=toggle_tag,
                        args=(tag,),
                        use_container_width=True,
                        type="primary",  # Highlight selected tags
                    )
                else:
                    cols_container[col].button(
                        tag,
                        key=f"unselected_{tag}",
                        on_click=toggle_tag,
                        args=(tag,),
                        use_container_width=True,
                        type="secondary",  # Default for unselected tags
                    )
                tag_index += 1

                
def find_closest_matches_content(selected_tags, flavor_tags_list, dataset, base_type, threshold=0.3):
    # Base Type 우선으로 데이터 필터링 해봄
    filtered_dataset = dataset[dataset['Base Type'] == base_type]
    flavor_tags_list_filtered = filtered_dataset['Flavor Tags'].tolist()

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(flavor_tags_list_filtered)
    query_vector = vectorizer.transform([', '.join(selected_tags)])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # 0.3 이상의 임계값을 넘지 못하면 추천 가능한 태그 없음이라고 띄우기~!
    top_indices = [i for i, sim in enumerate(similarities) if sim >= threshold]

    if not top_indices:
        return None, False 

    return filtered_dataset.iloc[top_indices], True

# Recommend drinks based on selected flavor tags
def recommend_drinks(selected_tags, flavor_tags_list, dataset):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(flavor_tags_list)
    query_vector = vectorizer.transform([', '.join(selected_tags)])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-5:][::-1]
    return [dataset.iloc[i]["Menu"] for i in top_indices]


# KNN Page
def knn_page():
    st.title("KNN Recommendation Model")
    dataset = load_data()

    base_type = st.selectbox("Select Base Type", dataset['Base Type'].unique())
    st.write("### Select Flavor Tags")
    flavor_tags = sorted(set(', '.join(dataset['Flavor Tags']).split(', ')))
    display_tags_in_grid(flavor_tags)

    selected_tags = st.session_state["selected_tags"]
    if st.button("Get Recommendations", type="primary"):
        if selected_tags:
            recommendations, has_recommendation = find_closest_matches_content(
                selected_tags,
                dataset['Flavor Tags'],
                dataset,
                base_type,
                threshold=0.3  
            )
            if has_recommendation:
                st.write("### Recommended Drinks")
                for menu in recommendations['Menu']:
                    st.write(f"- {menu}")
            else:
                st.write("✔️ No matching drinks found for the selected tags. Try different tags.")
        else:
            st.write("🥺☝🏻 Please select at least one flavor tag.")

# Content-Based Filtering Page
def content_based_page():
    st.title("Content-Based Filtering Model")
    dataset = load_data()

    base_type = st.selectbox("Select Base Type", dataset['Base Type'].unique())
    st.write("### Select Flavor Tags")
    flavor_tags = sorted(set(', '.join(dataset['Flavor Tags']).split(', ')))
    display_tags_in_grid(flavor_tags)

    selected_tags = st.session_state["selected_tags"]
    if st.button("Get Recommendations", type="primary"):
        if selected_tags:
            # Content-based filtering 로직에 임계값 추가
            recommendations, has_recommendation = find_closest_matches_content(
                selected_tags,
                dataset['Flavor Tags'],
                dataset,
                base_type,
                threshold=0.3  # 유사도 기준 설정
            )
            if has_recommendation:
                st.write("### Recommended Drinks")
                for menu in recommendations['Menu']:
                    st.write(f"- {menu}")
            else:
                st.write("✔️ No matching drinks found for the selected tags. Try different tags.")
        else:
            st.write("🥺☝🏻 Please select at least one flavor tag.")

# MLP Page
def mlp_page():
    st.title("MLP Classification Model")
    dataset = load_data()

    base_type = st.selectbox("Select Base Type", dataset['Base Type'].unique())
    st.write("### Select Flavor Tags")
    flavor_tags = sorted(set(', '.join(dataset['Flavor Tags']).split(', ')))
    display_tags_in_grid(flavor_tags)

    selected_tags = st.session_state["selected_tags"]
    le = LabelEncoder()
    dataset['Base Type Encoded'] = le.fit_transform(dataset['Base Type'])
    X = pd.get_dummies(dataset[['Base Type Encoded', 'Contains Caffeine', 'Contains Gluten']])
    y = dataset['Menu']

    x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    mlp = MLPClassifier(hidden_layer_sizes=(50,), max_iter=500, random_state=42)
    mlp.fit(x_train, y_train)

    input_dict = {
        'Base Type Encoded': le.transform([base_type])[0],
        'Contains Caffeine': 1, 
        'Contains Gluten': 0   
    }

    input_df = pd.DataFrame([input_dict])
    input_features = pd.get_dummies(input_df).reindex(columns=X.columns, fill_value=0)

    if st.button("Recommend Menu", type="primary", use_container_width=True):
        prediction = mlp.predict(input_features)
        st.write("### Recommended Drink")
        st.write(prediction[0])



def main():
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Select a page", ("KNN Model", "Content-Based Filtering", "MLP Model"))

    if page == "KNN Model":
        knn_page()
    elif page == "Content-Based Filtering":
        content_based_page()
    elif page == "MLP Model":
        mlp_page()

if __name__ == "__main__":
    main()
