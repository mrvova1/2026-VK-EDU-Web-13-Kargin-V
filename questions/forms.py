import re

from django import forms
from django.db import transaction
from django.utils.text import slugify

from .models import Answer, Question, Tag


class QuestionForm(forms.ModelForm):
    tags = forms.CharField(
        label="Теги",
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "#django #python",
        }),
    )

    class Meta:
        model = Question
        fields = ("title", "text")
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Заголовок вопроса",
            }),
            "text": forms.Textarea(attrs={
                "class": "form-control form-control-lg",
                "rows": 8,
                "placeholder": "Текст вопроса",
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_tags(self):
        raw = self.cleaned_data.get("tags", "")
        tokens = re.split(r"[,\s]+", raw.strip())
        cleaned = []
        for token in tokens:
            token = token.strip().lstrip("#").strip()
            if token and token not in cleaned:
                cleaned.append(token)
        return cleaned

    def save(self, commit=True):
        if not self.user:
            raise ValueError("QuestionForm.save() requires user.")
        question = super().save(commit=False)
        question.author = self.user

        if commit:
            with transaction.atomic():
                question.save()
                tags = []
                for tag_name in self.cleaned_data.get("tags", []):
                    tag_slug = slugify(tag_name)
                    tag, _ = Tag.objects.get_or_create(
                        slug=tag_slug,
                        defaults={"name": tag_name},
                    )
                    tags.append(tag)
                question.tags.set(tags)

        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ("text",)
        widgets = {
            "text": forms.Textarea(attrs={
                "class": "form-control form-control-lg",
                "rows": 5,
                "placeholder": "Ваш ответ",
            }),
        }

    def __init__(self, *args, question=None, author=None, **kwargs):
        self.question = question
        self.author = author
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        if not self.question or not self.author:
            raise ValueError("AnswerForm.save() requires question and author.")
        answer = super().save(commit=False)
        answer.question = self.question
        answer.author = self.author
        if commit:
            answer.save()
        return answer


class QuestionVoteForm(forms.Form):
    question_id = forms.IntegerField(min_value=1)
    vote_type = forms.ChoiceField(choices=(("like", "like"), ("dislike", "dislike")))


class AnswerVoteForm(forms.Form):
    answer_id = forms.IntegerField(min_value=1)
    vote_type = forms.ChoiceField(choices=(("like", "like"), ("dislike", "dislike")))


class CorrectAnswerForm(forms.Form):
    question_id = forms.IntegerField(min_value=1)
    answer_id = forms.IntegerField(min_value=1)