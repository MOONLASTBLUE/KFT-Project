import streamlit as st
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

def load_data():
    dataset = pd.read_csv('KFT Dataset.csv')
    dataset['Flavor Tags'] = dataset['Flavor Tags'].fillna('').apply(lambda x: ', '.join(set(x.split(', '))))
    return dataset

# Tag selection -> 빡세ㅔ네 . . . . .
if "selected_tags" not in st.session_state:
    st.session_state["selected_tags"] = []

def toggle_tag(tag):
    if tag in st.session_state["selected_tags"]:
        st.session_state["selected_tags"].remove(tag)
    else:
        st.session_state["selected_tags"].append(tag)

def display_tags_in_grid(tags, cols=5):
    """Display tags in a grid layout with the specified number of columns."""
    rows = len(tags) // cols + (1 if len(tags) % cols != 0 else 0)
    tag_index = 0
    for row in range(rows):
        cols_container = st.columns(cols)
        for col in range(cols):
            if tag_index < len(tags):
                tag = tags[tag_index]
                if tag in st.session_state["selected_tags"]:
                    cols_container[col].button(tag, key=f"selected_{tag}", on_click=toggle_tag, args=(tag,))
                else:
                    cols_container[col].button(tag, key=f"unselected_{tag}", on_click=toggle_tag, args=(tag,))
                tag_index += 1

# 가까운 태그 매칭~
def find_closest_matches(selected_tags, flavor_tags_list):
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(flavor_tags_list)
    query_vector = vectorizer.transform([', '.join(selected_tags)])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-5:][::-1]
    return top_indices

# KNN Page
def knn_page():
    st.title("KNN Recommendation Model")
    dataset = load_data()

    base_type = st.selectbox("Select Base Type", dataset['Base Type'].unique())
    st.write("### Select Flavor Tags")
    flavor_tags = sorted(set(', '.join(dataset['Flavor Tags']).split(', ')))
    display_tags_in_grid(flavor_tags)

    selected_tags = st.session_state["selected_tags"]
    if selected_tags:
        closest_indices = find_closest_matches(selected_tags, dataset['Flavor Tags'])

        st.write("### Recommended Drinks")
        for i in closest_indices:
            st.write(dataset.iloc[i]['Menu'])

# Content-Based Filtering Page
def content_based_page():
    st.title("Content-Based Filtering Model")
    dataset = load_data()

    base_type = st.selectbox("Select Base Type", dataset['Base Type'].unique())
    st.write("### Select Flavor Tags")
    flavor_tags = sorted(set(', '.join(dataset['Flavor Tags']).split(', ')))
    display_tags_in_grid(flavor_tags)

    selected_tags = st.session_state["selected_tags"]
    if selected_tags:
        closest_indices = find_closest_matches(selected_tags, dataset['Flavor Tags'])

        st.write("### Recommended Drinks")
        for i in closest_indices:
            st.write(dataset.iloc[i]['Menu'])

# MLP Page
def mlp_page():
    st.title("MLP Classification Model")
    dataset = load_data()

    base_type = st.selectbox("Select Base Type", dataset['Base Type'].unique())
    st.write("### Select Flavor Tags")
    flavor_tags = sorted(set(', '.join(dataset['Flavor Tags']).split(', ')))
    display_tags_in_grid(flavor_tags)

    selected_tags = st.session_state["selected_tags"]
    if selected_tags:
        le = LabelEncoder()
        dataset['Base Type Encoded'] = le.fit_transform(dataset['Base Type'])
        x = pd.get_dummies(dataset[['Base Type Encoded', 'Contains Caffeine', 'Contains Gluten']])
        y = dataset['Menu']

        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=42)

        mlp = MLPClassifier(hidden_layer_sizes=(50,), max_iter=500, random_state=42)
        mlp.fit(x_train, y_train)

        input_data = [le.transform([base_type])[0]] + [1 if tag in selected_tags else 0 for tag in flavor_tags]
        prediction = mlp.predict([input_data])

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
