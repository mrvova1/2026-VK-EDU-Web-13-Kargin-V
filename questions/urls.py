from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("hot/", views.hot, name="hot"),
    path("search/", views.search, name="search"),
    path("tag/<slug:tag_slug>/", views.tag, name="tag"),
    path("question/<int:question_id>/", views.question, name="question"),
    path("user/<str:username>/", views.user_profile, name="user_profile"),

    path("ajax/question-vote/", views.question_vote, name="ajax_question_vote"),
    path("ajax/answer-vote/", views.answer_vote, name="ajax_answer_vote"),
    path("ajax/correct-answer/", views.correct_answer, name="ajax_correct_answer"),
]