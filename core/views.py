from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from questions.forms import QuestionForm
from questions.models import Profile

from .forms import LoginForm, ProfileForm, SignupForm


def login_view(request):
    form = LoginForm(
        request.POST or None,
        request=request,
        initial={"next": request.GET.get("next", "")},
    )

    if request.method == "POST" and form.is_valid():
        user = authenticate(
            request,
            username=form.cleaned_data["username"],
            password=form.cleaned_data["password"],
        )
        if user is not None:
            login(request, user)
            next_url = form.cleaned_data.get("next") or reverse("home")
            return redirect(next_url)
        form.add_error(None, "Неверный логин или пароль.")

    return render(request, "core/login.html", {
        "page_title": "Логин",
        "form": form,
    })


def signup_view(request):
    form = SignupForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("home")

    return render(request, "core/signup.html", {
        "page_title": "Регистрация",
        "form": form,
    })


@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=profile, user=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        return redirect("profile")

    return render(request, "core/profile.html", {
        "page_title": "Профиль",
        "form": form,
        "profile": profile,
    })


@login_required
def ask_view(request):
    form = QuestionForm(request.POST or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        question = form.save()
        return redirect(question.get_absolute_url())

    return render(request, "core/ask.html", {
        "page_title": "Задать вопрос",
        "form": form,
    })


@login_required
def logout_view(request):
    next_url = request.POST.get("next") or request.GET.get("next") or reverse("home")
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("home")

    logout(request)
    return redirect(next_url)