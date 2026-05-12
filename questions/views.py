from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.forms import LoginForm
from .forms import AnswerForm
from .models import Profile, Question, Tag
from .utils import paginate


def index(request):
    questions = Question.objects.new()
    page = paginate(questions, request, per_page=10)
    return render(
        request,
        "core/index.html",
        {
            "page_obj": page,
            "questions": page.object_list,
            "page_title": "Новые вопросы",
            "page_heading": "Новые вопросы",
        },
    )


def hot(request):
    questions = Question.objects.hot()
    page = paginate(questions, request, per_page=10)
    return render(
        request,
        "core/hot.html",
        {
            "page_obj": page,
            "questions": page.object_list,
            "page_title": "Лучшие вопросы",
            "page_heading": "Лучшие вопросы",
        },
    )


def search(request):
    query = request.GET.get("q", "").strip()
    questions = Question.objects.search(query)
    page = paginate(questions, request, per_page=10)
    return render(
        request,
        "core/index.html",
        {
            "page_obj": page,
            "questions": page.object_list,
            "page_title": f"Поиск: {query}" if query else "Поиск",
            "page_heading": f"Результаты поиска: {query}" if query else "Поиск",
        },
    )


def tag(request, tag_slug):
    tag_obj = get_object_or_404(Tag, slug=tag_slug)
    questions = Question.objects.by_tag(tag_slug)
    page = paginate(questions, request, per_page=10)
    return render(
        request,
        "core/tag.html",
        {
            "page_obj": page,
            "questions": page.object_list,
            "tag": tag_obj,
            "page_title": f"Тег #{tag_obj.name}",
            "page_heading": f"Тег: #{tag_obj.name}",
        },
    )


def question(request, question_id):
    question_item = get_object_or_404(
        Question.objects.with_related(),
        pk=question_id,
    )
    answers_qs = question_item.answers.select_related("author").all()

    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.get_full_path()}")

        form = AnswerForm(request.POST, question=question_item, author=request.user)
        if form.is_valid():
            answer = form.save()
            ordered_ids = list(
                question_item.answers.order_by(
                    "-is_correct",
                    "-rating",
                    "-created_at",
                    "-id",
                ).values_list("id", flat=True)
            )
            position = ordered_ids.index(answer.id) + 1
            page_number = (position - 1) // 10 + 1
            return redirect(
                f"{question_item.get_absolute_url()}?page={page_number}#answer-{answer.id}"
            )
    else:
        form = AnswerForm(question=question_item, author=request.user if request.user.is_authenticated else None)

    page = paginate(answers_qs, request, per_page=10)
    return render(
        request,
        "core/question.html",
        {
            "question_item": question_item,
            "answers": page.object_list,
            "page_obj": page,
            "answer_form": form if request.user.is_authenticated else None,
            "page_title": question_item.title,
        },
    )


def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=user)

    user_questions = user.questions.select_related("author").prefetch_related("tags")
    page = paginate(user_questions, request, per_page=10)

    return render(
        request,
        "core/user_profile.html",
        {
            "profile_user": user,
            "profile": profile,
            "questions": page.object_list,
            "page_obj": page,
            "page_title": f"Пользователь {user.username}",
            "page_heading": f"Пользователь: {user.username}",
        },
    )