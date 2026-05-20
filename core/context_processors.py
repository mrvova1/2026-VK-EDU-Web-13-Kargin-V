from django.contrib.auth.models import User
from django.db.models import Count, F

from django.core.cache import cache
from questions.models import Tag


def sidebar_data(request):
    popular_tags = cache.get("popular_tags")
    if popular_tags is None:
        popular_tags = list(Tag.objects.popular()[:10])
        cache.set("popular_tags", popular_tags, 60*60)
    
    best_users = cache.get("best_users")
    if best_users is None:
        from django.contrib.auth.models import User
        from django.db.models import Count, F, Q
        from datetime import datetime, timedelta
        week_ago = datetime.now() - timedelta(days=7)
        best_users = list(
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
        cache.set("best_users", best_users, 60*60)
    
    return {"popular_tags": popular_tags, "best_users": best_users}