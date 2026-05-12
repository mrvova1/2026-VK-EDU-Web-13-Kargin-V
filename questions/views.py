from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from core.forms import LoginForm
from .forms import AnswerForm, AnswerVoteForm, CorrectAnswerForm, QuestionVoteForm
from .models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag
from .utils import paginate


def _json_error(message, status=400, code="error", **extra):
    payload = {
        "ok": False,
        "error": code,
        "message": message,
    }
    payload.update(extra)
    return JsonResponse(payload, status=status)


def _require_auth_json(request):
    if request.user.is_authenticated:
        return None
    return _json_error(
        "Требуется авторизация.",
        status=401,
        code="auth_required",
        redirect_url=f"{reverse('login')}?next={request.get_full_path()}",
    )


def _attach_vote_flags(items, vote_map):
    for item in items:
        item.user_vote = vote_map.get(item.id)


def _get_question_vote_map(user, question_ids):
    if not user.is_authenticated or not question_ids:
        return {}
    return dict(
        QuestionLike.objects.filter(user=user, question_id__in=question_ids)
        .values_list("question_id", "value")
    )


def _get_answer_vote_map(user, answer_ids):
    if not user.is_authenticated or not answer_ids:
        return {}
    return dict(
        AnswerLike.objects.filter(user=user, answer_id__in=answer_ids)
        .values_list("answer_id", "value")
    )


def _apply_vote(model, like_model, object_field, object_id, user, vote_type):
    new_value = 1 if vote_type == "like" else -1

    with transaction.atomic():
        obj = get_object_or_404(model, pk=object_id)
        like = (
            like_model.objects.select_for_update()
            .filter(user=user, **{f"{object_field}_id": object_id})
            .first()
        )

        if like is None:
            like_model.objects.create(user=user, **{object_field: obj}, value=new_value)
            delta = new_value
        else:
            old_value = like.value
            if old_value == new_value:
                return None, "already_voted"
            like.value = new_value
            like.save(update_fields=["value"])
            delta = new_value - old_value

        model.objects.filter(pk=obj.pk).update(rating=F("rating") + delta)
        obj.refresh_from_db(fields=["rating"])
        return obj, None


def index(request):
    questions = Question.objects.new()
    page = paginate(questions, request, per_page=10)
    question_list = list(page.object_list)
    _attach_vote_flags(question_list, _get_question_vote_map(request.user, [q.id for q in question_list]))

    return render(
        request,
        "core/index.html",
        {
            "page_obj": page,
            "questions": question_list,
            "page_title": "Новые вопросы",
            "page_heading": "Новые вопросы",
        },
    )


def hot(request):
    questions = Question.objects.hot()
    page = paginate(questions, request, per_page=10)
    question_list = list(page.object_list)
    _attach_vote_flags(question_list, _get_question_vote_map(request.user, [q.id for q in question_list]))

    return render(
        request,
        "core/hot.html",
        {
            "page_obj": page,
            "questions": question_list,
            "page_title": "Лучшие вопросы",
            "page_heading": "Лучшие вопросы",
        },
    )


def search(request):
    query = request.GET.get("q", "").strip()
    questions = Question.objects.search(query)
    page = paginate(questions, request, per_page=10)
    question_list = list(page.object_list)
    _attach_vote_flags(question_list, _get_question_vote_map(request.user, [q.id for q in question_list]))

    return render(
        request,
        "core/index.html",
        {
            "page_obj": page,
            "questions": question_list,
            "page_title": f"Поиск: {query}" if query else "Поиск",
            "page_heading": f"Результаты поиска: {query}" if query else "Поиск",
        },
    )


def tag(request, tag_slug):
    tag_obj = get_object_or_404(Tag, slug=tag_slug)
    questions = Question.objects.by_tag(tag_slug)
    page = paginate(questions, request, per_page=10)
    question_list = list(page.object_list)
    _attach_vote_flags(question_list, _get_question_vote_map(request.user, [q.id for q in question_list]))

    return render(
        request,
        "core/tag.html",
        {
            "page_obj": page,
            "questions": question_list,
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
    answer_list = list(page.object_list)

    question_vote_map = _get_question_vote_map(request.user, [question_item.id])
    answer_vote_map = _get_answer_vote_map(request.user, [a.id for a in answer_list])

    question_item.user_vote = question_vote_map.get(question_item.id)
    _attach_vote_flags(answer_list, answer_vote_map)

    return render(
        request,
        "core/question.html",
        {
            "question_item": question_item,
            "answers": answer_list,
            "page_obj": page,
            "answer_form": form if request.user.is_authenticated else None,
            "page_title": question_item.title,
            "can_choose_correct_answer": request.user.is_authenticated and question_item.author_id == request.user.id,
        },
    )


def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    profile, _ = Profile.objects.get_or_create(user=user)

    user_questions = user.questions.select_related("author").prefetch_related("tags")
    page = paginate(user_questions, request, per_page=10)
    question_list = list(page.object_list)
    _attach_vote_flags(question_list, _get_question_vote_map(request.user, [q.id for q in question_list]))

    return render(
        request,
        "core/user_profile.html",
        {
            "profile_user": user,
            "profile": profile,
            "questions": question_list,
            "page_obj": page,
            "page_title": f"Пользователь {user.username}",
            "page_heading": f"Пользователь: {user.username}",
        },
    )


def question_vote(request):
    if request.method != "POST":
        return _json_error("Недопустимый метод.", status=405, code="method_not_allowed")

    auth_error = _require_auth_json(request)
    if auth_error:
        return auth_error

    form = QuestionVoteForm(request.POST)
    if not form.is_valid():
        return _json_error("Неверные параметры.", status=400, code="invalid_data", errors=form.errors)

    question_id = form.cleaned_data["question_id"]
    vote_type = form.cleaned_data["vote_type"]

    question, error = _apply_vote(Question, QuestionLike, "question", question_id, request.user, vote_type)
    if error == "already_voted":
        return _json_error("Вы уже отправляли такой голос.", status=400, code="already_voted")

    return JsonResponse({"ok": True, "rating": question.rating, "question_id": question.id})


def answer_vote(request):
    if request.method != "POST":
        return _json_error("Недопустимый метод.", status=405, code="method_not_allowed")

    auth_error = _require_auth_json(request)
    if auth_error:
        return auth_error

    form = AnswerVoteForm(request.POST)
    if not form.is_valid():
        return _json_error("Неверные параметры.", status=400, code="invalid_data", errors=form.errors)

    answer_id = form.cleaned_data["answer_id"]
    vote_type = form.cleaned_data["vote_type"]

    answer, error = _apply_vote(Answer, AnswerLike, "answer", answer_id, request.user, vote_type)
    if error == "already_voted":
        return _json_error("Вы уже отправляли такой голос.", status=400, code="already_voted")

    return JsonResponse({"ok": True, "rating": answer.rating, "answer_id": answer.id})


def correct_answer(request):
    if request.method != "POST":
        return _json_error("Недопустимый метод.", status=405, code="method_not_allowed")

    auth_error = _require_auth_json(request)
    if auth_error:
        return auth_error

    form = CorrectAnswerForm(request.POST)
    if not form.is_valid():
        return _json_error("Неверные параметры.", status=400, code="invalid_data", errors=form.errors)

    question_id = form.cleaned_data["question_id"]
    answer_id = form.cleaned_data["answer_id"]

    question = get_object_or_404(Question, pk=question_id)
    if question.author_id != request.user.id:
        return _json_error(
            "Только автор вопроса может выбирать правильный ответ.",
            status=403,
            code="forbidden",
        )

    answer = get_object_or_404(Answer, pk=answer_id, question=question)

    with transaction.atomic():
        Answer.objects.filter(question=question, is_correct=True).exclude(pk=answer.pk).update(is_correct=False)
        if not answer.is_correct:
            answer.is_correct = True
            answer.save(update_fields=["is_correct"])

    answer.refresh_from_db(fields=["is_correct"])
    return JsonResponse(
        {
            "ok": True,
            "question_id": question.id,
            "answer_id": answer.id,
            "is_correct": answer.is_correct,
        }
    )
