from django.shortcuts import render


def login_view(request):
    return render(request, "core/login.html", {"page_title": "Логин"})


def signup_view(request):
    return render(request, "core/signup.html", {"page_title": "Регистрация"})


def profile_view(request):
    return render(request, "core/profile.html", {"page_title": "Профиль"})


def ask_view(request):
    return render(request, "core/ask.html", {"page_title": "Задать вопрос"})