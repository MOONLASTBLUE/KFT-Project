from django.shortcuts import render, redirect
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from myapp.models import User, Drink, Feedback
import pandas as pd
import uuid
from django.utils import timezone


def load_data():
    dataset = pd.read_csv('KFT Dataset_modified.csv')
    dataset['Flavor Tags'] = dataset['Flavor Tags'].fillna('').apply(lambda x: ', '.join(set(x.split(', '))))
    return dataset


def save_user_data(user_id, category, base_type, selected_tags, recommendations, feedback):
    user, created = User.objects.get_or_create(user_id=user_id)

    for rec, fb in zip(recommendations, feedback):
        Feedback.objects.create(
            user=user,
            category=category,
            base_type=base_type,
            selected_tags=selected_tags,
            recommendation=rec,
            # add timezone now
            created_at=timezone.now(),  
        )
    return "Data saved successfully!"


# def save_user_data(user_id, category, base_type, selected_tags, recommendations, feedback):
#     df = pd.DataFrame({
#         'UserID': [user_id] * len(recommendations),
#         'Category': [category] * len(recommendations),
#         'BaseType': [base_type] * len(recommendations),
#         'SelectedTags': [', '.join(selected_tags)] * len(recommendations),
#         'Recommendation': recommendations,
#         'Feedback': feedback,
#     })
#     df.to_csv('user_data.csv', mode='a', index=False, header=False)

# Content-Based Filtering
def content_based_recommend(selected_tags, dataset, base_type, threshold=0.3):
    filtered_dataset = dataset[dataset['Base Type'] == base_type]
    if filtered_dataset.empty:
        return [], False

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(filtered_dataset['Flavor Tags'])
    query_vector = vectorizer.transform([', '.join(selected_tags)])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

    top_indices = [i for i, sim in enumerate(similarities) if sim >= threshold]
    recommendations = filtered_dataset.iloc[top_indices]['Menu'].tolist() if top_indices else []
    return recommendations, bool(recommendations)

# 메인 페이지
def main_view(request):
    dataset = load_data()
    categories = dataset['Category'].unique()
    base_types = dataset['Base Type'].unique()
    flavor_tags = sorted(set(', '.join(dataset['Flavor Tags']).split(', ')))

    # 동의 체크 ㅠㅠ 근데 안뜸..
    consent_given = request.session.get("consent_given", False)

    if not consent_given:
        if request.method == "POST" and "consent" in request.POST:
            if request.POST.get("consent") == "yes":
                request.session["consent_given"] = True
                return redirect("main")
            else:
                return render(request, "main.html", {"error": "You must provide consent to proceed."})

        return render(
            request,
            "main.html",
            {
                "consent_given": False,
            },
        )

    # POST 
    if request.method == "POST":
        user_id = request.POST.get("user_id", str(uuid.uuid4())[:8])
        category = request.POST.get("category")
        base_type = request.POST.get("base_type")
        selected_tags = request.POST.getlist("tags")
        recommendations = []
        error_message = None

        # Recommedation
        if selected_tags and base_type:
            recommendations, has_recommendation = content_based_recommend(selected_tags, dataset, base_type)
            if not has_recommendation:
                error_message = "No matching drinks found. Try different tags."
        else:
            error_message = "Please select a category, base type, and at least one flavor tag."

        # User Data
        save_user_data(user_id, category, base_type, selected_tags, recommendations, feedback=[""] * len(recommendations))

        # Page Rendering
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
            },
        )

    # GET: Main Page Redering
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
            # get random user ID
            "user_id": str(uuid.uuid4())[:8],  
            "consent_given": True,
        },
    )

# save and submit feedbacks
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
