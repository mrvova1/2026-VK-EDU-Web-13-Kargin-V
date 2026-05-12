from django.conf import settings
from pathlib import Path
from uuid import uuid4

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse

from .managers import QuestionManager, TagManager


def avatar_upload_to(instance, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if not ext:
        ext = ".jpg"
    return f"avatars/{uuid4().hex}{ext}"


class Tag(models.Model):
    name = models.CharField("Название", max_length=64, unique=True)
    slug = models.SlugField("Slug", max_length=64, unique=True)

    objects = TagManager()

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Question(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Автор",
    )
    title = models.CharField("Заголовок", max_length=255)
    text = models.TextField("Текст")
    tags = models.ManyToManyField(Tag, related_name="questions", verbose_name="Теги", blank=True)
    rating = models.IntegerField("Рейтинг", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    objects = QuestionManager()

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("question", kwargs={"question_id": self.pk})


class Answer(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Вопрос",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Автор",
    )
    text = models.TextField("Текст")
    rating = models.IntegerField("Рейтинг", default=0)
    is_correct = models.BooleanField("Правильный ответ", default=False)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Ответ"
        verbose_name_plural = "Ответы"
        ordering = ["-is_correct", "-rating", "-created_at", "-id"]

    def __str__(self):
        return f"Ответ #{self.pk} на {self.question_id}"


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
        verbose_name="Пользователь",
    )
    nickname = models.CharField("Никнейм", max_length=64, blank=True)
    avatar = models.ImageField("Аватар", upload_to=avatar_upload_to, blank=True, null=True)
    bio = models.TextField("О себе", blank=True)

    class Meta:
        verbose_name = "Профиль"
        verbose_name_plural = "Профили"

    def __str__(self):
        return self.nickname or self.user.username


class QuestionLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="question_likes",
        verbose_name="Пользователь",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="Вопрос",
    )
    value = models.SmallIntegerField("Значение", default=1)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Лайк вопроса"
        verbose_name_plural = "Лайки вопросов"
        unique_together = (("user", "question"),)

    def __str__(self):
        return f"{self.user_id} -> {self.question_id}"


class AnswerLike(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="answer_likes",
        verbose_name="Пользователь",
    )
    answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        related_name="likes",
        verbose_name="Ответ",
    )
    value = models.SmallIntegerField("Значение", default=1)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Лайк ответа"
        verbose_name_plural = "Лайки ответов"
        unique_together = (("user", "answer"),)

    def __str__(self):
        return f"{self.user_id} -> {self.answer_id}"