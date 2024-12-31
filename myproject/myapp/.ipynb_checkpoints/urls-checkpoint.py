from django.urls import path
from . import views

urlpatterns = [
    path("", views.main_view, name="main"),
    path("submit_feedback/", views.submit_feedback, name="submit_feedback"),
]