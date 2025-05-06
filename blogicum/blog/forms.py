"""Формы для приложения 'blog'.

Этот модуль содержит формы для создания и редактирования постов,
добавления комментариев к постам и обновления информации о пользователе.
"""

from django import forms
from django.contrib.auth.models import User

from .models import Comment, Post


class PostForm(forms.ModelForm):
    """Форма для создания и редактирования постов блога."""

    class Meta:
        model = Post
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date'})
        }
        exclude = ('author',)


class CommentForm(forms.ModelForm):
    """Форма для добавления комментариев к постам блога.

    Автор комментария должен заполнить только поле текста,
    остальные поля, такие как автор и пост, заполняются автоматически.
    """

    class Meta:
        """
        Автор поздравления должен заполнить только поле text,
        а остальные поля должны заполняться автоматически.
        """

        model = Comment
        fields = ('text',)


class UserUpdateForm(forms.ModelForm):
    """Форма для обновления профиля пользователя."""

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
