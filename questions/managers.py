from django.db import models
from django.db.models import Count, Q


class QuestionQuerySet(models.QuerySet):
    def with_related(self):
        return (
            self.select_related("author")
            .prefetch_related("tags")
            .annotate(answers_count=Count("answers", distinct=True))
        )

    def new(self):
        return self.with_related().order_by("-created_at", "-id")

    def hot(self):
        return self.with_related().order_by("-rating", "-created_at", "-id")

    def by_tag(self, tag_slug):
        return self.with_related().filter(tags__slug=tag_slug).distinct()

    def search(self, query):
        if not query:
            return self.new()

        return self.with_related().filter(
            Q(title__icontains=query)
            | Q(text__icontains=query)
            | Q(tags__name__icontains=query)
        ).distinct()


class QuestionManager(models.Manager.from_queryset(QuestionQuerySet)):
    pass


class TagManager(models.Manager):
    def popular(self):
        return (
            self.annotate(questions_count=Count("questions", distinct=True))
            .order_by("-questions_count", "name")
        )