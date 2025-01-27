from django.shortcuts import render, redirect
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from myapp.models import User, Feedback
import pandas as pd
import uuid
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

def load_data():
    dataset = pd.read_csv('KFT Dataset_modified.csv')
    dataset['Flavor Tags'] = dataset['Flavor Tags'].fillna('')
    dataset['Base Type'] = dataset['Base Type'].fillna('')

    def process_base_type(base_type):
        items = [item.strip() for item in base_type.split(',')]
        return ', '.join(sorted(set(items)))
    dataset['Base Type'] = dataset['Base Type'].apply(process_base_type)

    dataset['Combined Features'] = dataset['Flavor Tags'] + ' ' + dataset['Base Type'].str.replace(',', ' ')
    return dataset

def save_user_data(user_id, category, base_type, selected_tags, recommendations):
    user, created = User.objects.get_or_create(user_id=user_id)
    for rec in recommendations:
        Feedback.objects.create(
            user=user,
            category=category,
            base_type=base_type,
            selected_tags=selected_tags,
            recommendation=rec,
            created_at=timezone.now(),
        )
    return "Data saved successfully!"


def content_based_recommend(selected_tags, dataset, base_type, preferences, threshold=0.3):
    # Base Type을 분리 -> 리스트로 만듦
    base_type_list = base_type.split(', ')

    for column, value in preferences.items():
        if value == "Yes":
            dataset = dataset[dataset[column] == "Yes"]

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(dataset['Combined Features'])
    query_vector = vectorizer.transform([', '.join(selected_tags + base_type_list)])

    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # 유사도 점수:  데이터프레임에 추가
    dataset = dataset.copy()  # 원본 데이터프레임 보호하기 위함임
    dataset['Similarity Score'] = similarities

    # 유사도가 기준치를 초과 -> 추천 항목 선택
    top_indices = [i for i, sim in enumerate(similarities) if sim >= threshold]

    # 상위 5개의 추천 결과만 반환
    recommendations = dataset.iloc[top_indices].nlargest(5, 'Similarity Score')['Menu'].tolist() if top_indices else []
    return recommendations, bool(recommendations)


@csrf_protect
def main_view(request):
    dataset = load_data()
    categories = dataset['Category'].unique()
    
    # Base Type 값을 쉼표로 분리한 후 유니크 값으로 변환
    base_types = sorted(set(', '.join(dataset['Base Type']).split(', ')))
    flavor_tags = sorted(set(', '.join(dataset['Flavor Tags']).split(', ')))

    # 추가된 Yes/No 필터 컬럼들
    preference_columns = [
        "Customizable Sweetness",
        "Contains Caffeine",
        "Contains Gluten",
        "Oat Milk Substitution",
        "Vegan-friendly",
        "Contains dairy"
    ]

    consent_given = request.session.get("consent_given", False)

    if not consent_given:
        if request.method == "POST" and "consent" in request.POST:
            if request.POST.get("consent") == "yes":
                request.session["consent_given"] = True
                return redirect("main")
            else:
                return render(request, "main.html", {"error": "You must provide consent to proceed."})

        return render(request, "main.html", {"consent_given": False})

    if request.method == "POST":
        user_id = request.POST.get("user_id", str(uuid.uuid4())[:8])
        category = request.POST.get("category")
        base_type = request.POST.get("base_type")
        selected_tags = request.POST.getlist("tags")
        recommendations = []
        error_message = None

        # 유저가 선택한 Yes/No 옵션 수집
        preferences = {col: request.POST.get(col) for col in preference_columns}

        if selected_tags and base_type:
            recommendations, has_recommendation = content_based_recommend(selected_tags, dataset, base_type, preferences)
            if not has_recommendation:
                error_message = "No matching drinks found. Try different tags."
        else:
            error_message = "Please select a category, base type, and at least one flavor tag."

        if recommendations:
            save_user_data(user_id, category, base_type, selected_tags, recommendations)

        return render(
            request,
            "main.html",
            {
                "categories": categories,
                "base_types": base_types,
                "flavor_tags": flavor_tags,
                "recommendations": recommendations,
                "selected_tags": selected_tags,
                "category": category,
                "base_type": base_type,
                "error": error_message,
                "user_id": user_id,
                "consent_given": True,
                "preferences": preferences,
                "preference_columns": preference_columns,
            },
        )

    return render(
        request,
        "main.html",
        {
            "categories": categories,
            "base_types": base_types,
            "flavor_tags": flavor_tags,
            "recommendations": None,
            "selected_tags": [],
            "category": None,
            "base_type": None,
            "error": None,
            "user_id": str(uuid.uuid4())[:8],
            "consent_given": True,
            "preferences": {col: "No" for col in preference_columns},  # 초기값
            "preference_columns": preference_columns,
        },
    )

@csrf_protect
def submit_feedback(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        feedback_data = []
        for key, value in request.POST.items():
            if key.startswith("rating_"):
                index = key.split("_")[1]
                feedback_data.append(
                    {
                        "item": request.POST.get(f"recommendation_{index}"),
                        "rating": value,
                        "purchased": request.POST.get(f"purchased_{index}") == "on",
                    }
                )
        return render(request, "thank_you.html")
