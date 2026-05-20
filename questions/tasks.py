from celery import shared_task
from django.core.cache import cache
from django.db.models import Count, F, Q
from django.contrib.auth.models import User
from questions.models import Tag
from datetime import datetime, timedelta

@shared_task
def update_popular_tags_cache():
    """10 тегов с наибольшим количеством вопросов за последние 3 месяца"""
    three_months_ago = datetime.now() - timedelta(days=90)
    tags = (
        Tag.objects.filter(questions__created_at__gte=three_months_ago)
        .annotate(questions_count=Count("questions"))
        .order_by("-questions_count", "name")[:10]
    )
    cache.set("popular_tags", list(tags), timeout=60*60*6)
    return len(tags)

@shared_task
def update_best_users_cache():
    """10 пользователей с наибольшей активностью (вопросы+ответы) за последнюю неделю"""
    week_ago = datetime.now() - timedelta(days=7)
    users = (
        User.objects.filter(
            Q(questions__created_at__gte=week_ago) | Q(answers__created_at__gte=week_ago)
        )
        .annotate(
            questions_count=Count("questions", filter=Q(questions__created_at__gte=week_ago)),
            answers_count=Count("answers", filter=Q(answers__created_at__gte=week_ago))
        )
        .annotate(total=F("questions_count") + F("answers_count"))
        .filter(total__gt=0)
        .order_by("-total", "username")[:10]
    )
    cache.set("best_users", list(users), timeout=60*60*6)
    return len(users)

import requests
from django.conf import settings

@shared_task
def send_new_answer_notification(question_id, answer_data):
    """Отправляет событие в centrifugo о новом ответе"""
    channel = f"{settings.CENTRIFUGO_NAMESPACE}:{question_id}"
    headers = {
        "X-API-Key": settings.CENTRIFUGO_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "channel": channel,
        "data": answer_data,
    }
    url = f"{settings.CENTRIFUGO_URL}/api/publish"
    try:
        requests.post(url, json=payload, headers=headers, timeout=5)
    except Exception as e:
        pass


from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_new_answer_email(question_title, author_email, answer_preview, question_url):
    subject = f"Новый ответ на ваш вопрос: {question_title}"
    message = f"""
    Здравствуйте!

    На ваш вопрос "{question_title}" поступил новый ответ:
    "{answer_preview}"

    Посмотреть ответ: {question_url}

    С уважением,
    Команда EDU-Web
    """
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [author_email])