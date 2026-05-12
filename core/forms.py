from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.http import url_has_allowed_host_and_scheme

from questions.models import Profile

User = get_user_model()

from pathlib import Path

MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

class LoginForm(forms.Form):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "username",
            "placeholder": "Логин",
        }),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "current-password",
            "placeholder": "Пароль",
        }),
    )
    next = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean_next(self):
        next_url = self.cleaned_data.get("next") or ""
        if not next_url:
            return ""
        if self.request and url_has_allowed_host_and_scheme(
            url=next_url,
            allowed_hosts={self.request.get_host()},
            require_https=self.request.is_secure(),
        ):
            return next_url
        return ""


class SignupForm(forms.Form):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "username",
            "placeholder": "Логин",
        }),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "email",
            "placeholder": "name@example.com",
        }),
    )
    first_name = forms.CharField(
        label="Имя",
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "given-name",
            "placeholder": "Имя",
        }),
    )
    password1 = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "new-password",
            "placeholder": "Пароль",
        }),
    )
    password2 = forms.CharField(
        label="Повтор пароля",
        widget=forms.PasswordInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "new-password",
            "placeholder": "Повтор пароля",
        }),
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            self.add_error("password2", "Пароли не совпадают.")
            return cleaned_data

        if password1:
            user_for_validation = User(
                username=cleaned_data.get("username", ""),
                email=cleaned_data.get("email", ""),
                first_name=cleaned_data.get("first_name", ""),
            )
            try:
                validate_password(password1, user=user_for_validation)
            except forms.ValidationError as exc:
                self.add_error("password1", exc)

        return cleaned_data

    def save(self):
        user = User.objects.create_user(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            first_name=self.cleaned_data["first_name"],
            password=self.cleaned_data["password1"],
        )
        profile, _ = Profile.objects.get_or_create(user=user)
        if not profile.nickname:
            profile.nickname = user.first_name or user.username
            profile.save(update_fields=["nickname"])
        return user


class ProfileForm(forms.ModelForm):
    username = forms.CharField(
        label="Логин",
        widget=forms.TextInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "username",
        }),
    )
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "class": "form-control form-control-lg",
            "autocomplete": "email",
        }),
    )
    avatar = forms.ImageField(
        label="Аватар",
        required=False,
        widget=forms.ClearableFileInput(attrs={
            "class": "form-control form-control-lg",
            "accept": "image/*",
        }),
    )

    class Meta:
        model = Profile
        fields = ("nickname", "avatar")
        widgets = {
            "nickname": forms.TextInput(attrs={
                "class": "form-control form-control-lg",
                "placeholder": "Никнейм",
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields["username"].initial = user.username
            self.fields["email"].initial = user.email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        exists = User.objects.exclude(pk=self.user.pk).filter(username__iexact=username).exists()
        if exists:
            raise forms.ValidationError("Пользователь с таким логином уже существует.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        exists = User.objects.exclude(pk=self.user.pk).filter(email__iexact=email).exists()
        if exists:
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar

        ext = Path(avatar.name).suffix.lower()
        if ext not in ALLOWED_AVATAR_EXTENSIONS:
            raise forms.ValidationError(
                "Недопустимый формат файла. Разрешены JPG, JPEG, PNG, GIF и WEBP."
            )

        if avatar.size > MAX_AVATAR_SIZE:
            raise forms.ValidationError("Файл слишком большой. Максимум — 2 МБ.")

        return avatar

    def save(self, commit=True):
        profile = super().save(commit=False)
        profile.user = self.user

        if commit:
            self.user.username = self.cleaned_data["username"]
            self.user.email = self.cleaned_data["email"]
            self.user.save(update_fields=["username", "email"])
            profile.save()
            self.save_m2m()

        return profile