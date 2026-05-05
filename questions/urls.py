from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("hot/", views.hot, name="hot"),
    path("search/", views.search, name="search"),
    path("tag/<slug:tag_slug>/", views.tag, name="tag"),
    path("question/<int:question_id>/", views.question, name="question"),
    path("user/<str:username>/", views.user_profile, name="user_profile"),
]