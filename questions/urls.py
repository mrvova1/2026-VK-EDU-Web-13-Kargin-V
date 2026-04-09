from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path("hot/", views.hot, name="hot"),
    path("tag/<str:tag>/", views.tag, name="tag"),
    path("question/<int:question_id>/", views.question, name="question"),
]