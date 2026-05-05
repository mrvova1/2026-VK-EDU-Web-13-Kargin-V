from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import Answer, AnswerLike, Profile, Question, QuestionLike, Tag


class ProfileInline(admin.StackedInline):
    model = Profile
    fk_name = "user"
    can_delete = False
    extra = 0
    verbose_name = "Профиль"
    verbose_name_plural = "Профиль"


class AnswerInline(admin.TabularInline):
    model = Answer
    fk_name = "question"
    extra = 0
    raw_id_fields = ("author",)
    fields = ("author", "text", "rating", "is_correct", "created_at")
    readonly_fields = ("created_at",)


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ("username", "email", "is_staff", "is_active")
    search_fields = ("username", "email")


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "rating", "created_at", "answers_count")
    search_fields = ("title", "text", "author__username", "tags__name")
    list_filter = ("created_at", "rating", "tags")
    raw_id_fields = ("author",)
    filter_horizontal = ("tags",)
    inlines = (AnswerInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("author").prefetch_related("tags")

    @admin.display(description="Ответов")
    def answers_count(self, obj):
        return obj.answers.count()


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("id", "question", "author", "rating", "is_correct", "created_at")
    search_fields = ("text", "author__username", "question__title")
    list_filter = ("is_correct", "created_at", "rating")
    raw_id_fields = ("question", "author")
    list_select_related = ("question", "author")


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "nickname")
    search_fields = ("user__username", "nickname")
    raw_id_fields = ("user",)


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "value", "created_at")
    search_fields = ("user__username", "question__title")
    list_filter = ("created_at",)
    raw_id_fields = ("user", "question")


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ("user", "answer", "value", "created_at")
    search_fields = ("user__username", "answer__text")
    list_filter = ("created_at",)
    raw_id_fields = ("user", "answer")


admin.site.unregister(User)
admin.site.register(User, UserAdmin)