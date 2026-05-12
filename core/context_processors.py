from django.contrib.auth.models import User
from django.db.models import Count, F

from questions.models import Tag


def sidebar_data(request):
    popular_tags = Tag.objects.popular()[:10]

    best_users = (
        User.objects.annotate(
            questions_count=Count("questions", distinct=True),
            answers_count=Count("answers", distinct=True),
        )
        .annotate(total_activity=F("questions_count") + F("answers_count"))
        .order_by("-total_activity", "username")[:10]
    )

    return {
        "popular_tags": popular_tags,
        "best_users": best_users,
    }