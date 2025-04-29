"""
Модуль с классами представлений для работы с комментариями.

Содержит миксины и базовые классы для ограничения доступа и управления
комментариями, обеспечивая проверку аутентификации и авторства.
"""

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect
from django.urls import reverse

from .models import Comment


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин для ограничения доступа к объекту только его автору.

    Проверяет, является ли текущий пользователь автором объекта. Используется
    для защиты операций редактирования и удаления постов и комментариев.
    """

    def test_func(self):
        """
        Проверяет, является ли текущий пользователь автором объекта.

        Возвращает True, если пользователь является автором, иначе False.
        """
        return self.get_object().author == self.request.user

    def handle_no_permission(self):
        """
        Перенаправляет пользователя на страницу поста,
        если у него нет разрешения.

        Используется, когда пользователь не является автором объекта.
        """
        return redirect('blog:post_detail', self.kwargs['post_id'])


class CommentMixin(LoginRequiredMixin, OnlyAuthorMixin):
    """
    Базовый класс для представлений, работающих с комментариями.

    Обеспечивает общую логику для редактирования и удаления комментариев,
    включая проверку аутентификации и авторства.
    """

    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        """
        Возвращает URL для перенаправления после успешного выполнения действия.

        Перенаправляет пользователя на страницу поста,
        к которому относится комментарий.
        """
        return reverse('blog:post_detail', args=[self.object.post.pk])
