"""
Веб-представления для блог-приложения.

Этот модуль содержит классы представлений Django, реализующие функциональность
для работы с постами, категориями, комментариями, профилями пользователей.
Используются функция для фильтрации опубликованных постов
и ограничения доступа, а также generic views для упрощения обработки запросов.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostForm, UserUpdateForm
from .mixins import CommentMixin, OnlyAuthorMixin
from .models import Category, Comment, Post

PAGINATE_BY = 10


def post_set_processing(
        posts,
        apply_filtering=True,
        select_related_fields=None,
        annotate_comment_count=False
):
    """Обрабатывает список постов.

    Применяет фильтрацию по дате и статусу публикации, подключает связанные
    таблицы (author, category и т.п.), а также добавляет количество
    комментариев, если это нужно.

    Используется для подготовки списка постов перед выводом.
    """
    if apply_filtering:
        posts = posts.filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )
    if select_related_fields:
        posts = posts.select_related(*select_related_fields)
    if annotate_comment_count:
        posts = posts.annotate(comment_count=Count('comments'))
    return posts


class HomePageListView(ListView):
    """
    Главная страница с отсортированным списком опубликованных постов.

    Отображает список постов с пагинацией (10 постов на страницу), аннотируя
    количество комментариев и сортируя по убыванию даты публикации.
    """

    model = Post
    paginate_by = 10
    template_name = 'blog/index.html'

    def get_queryset(self):
        return post_set_processing(
            super().get_queryset(),
            annotate_comment_count=True
        ).order_by(*self.model._meta.ordering)


class PostDetailView(DetailView):
    """
    Страница детального просмотра поста.

    Отображает информацию о конкретном посте, включая форму для добавления
    комментариев и список существующих комментариев. Доступ к неопубликованным
    постам ограничен для всех, кроме автора.
    """

    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        full_qs = Post.objects.select_related(
            'author', 'category', 'location'
        )
        post = super().get_object(queryset=full_qs)
        if post.author != self.request.user:
            pub_qs = full_qs.filter(
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now()
            )
            post = super().get_object(queryset=pub_qs)
        return post

    def get_context_data(self, **kwargs):
        """Добавляет форму комментариев и список комментариев в контекст."""
        return super().get_context_data(
            **kwargs,
            form=CommentForm(),
            comments=self.object.comments.order_by('created_at')
        )


class PostCreateView(LoginRequiredMixin, CreateView):
    """
    Страница создания нового поста.

    Доступна только авторизованным пользователям. После создания поста
    пользователь перенаправляется на страницу своего профиля.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile', args=[self.request.user.username]
        )


class PostUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    """
    Страница редактирования поста.

    Доступна только автору поста. Неавторизованные пользователи
    перенаправляются на страницу поста. После редактирования пользователь
    возвращается на страницу поста.
    """

    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            form=PostForm(instance=self.object)
        )

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get(self.pk_url_kwarg)]
        )


class PostDeleteView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    """
    Страница удаления поста.

    Доступна только автору поста. После удаления пользователь перенаправляется
    на главную страницу.
    """

    model = Post
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')
    pk_url_kwarg = 'post_id'


class CategoryPostsView(ListView):
    """
    Страница со списком постов по выбранной категории.

    Отображает только посты из опубликованной категории с пагинацией
    (10 постов на страницу). Категория определяется по slug из URL.
    """

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = PAGINATE_BY

    def get_category(self):
        """Возвращает опубликованную категорию по slug из URL."""
        return get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )

    def get_queryset(self):
        return post_set_processing(
            self.get_category().posts.all(),
            apply_filtering=True,
            select_related_fields=['author', 'category'],
            annotate_comment_count=False
        )

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            category=self.get_category()
        )


class CommentCreateView(LoginRequiredMixin, CreateView):
    """
    Страница создания комментария к посту.

    Доступна только авторизованным пользователям. После создания комментария
    пользователь перенаправляется на страницу поста.
    """

    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            Post,
            pk=self.kwargs.get('post_id')
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            args=[self.kwargs.get('post_id')]
        )


class CommentUpdateView(CommentMixin, UpdateView):
    """
    Страница редактирования комментария.

    Доступна только автору комментария. После редактирования пользователь
    перенаправляется на страницу поста, к которому относится комментарий.
    """

    form_class = CommentForm


class CommentDeleteView(CommentMixin, DeleteView):
    """
    Страница удаления комментария.

    Доступна только автору комментария. После удаления пользователь
    перенаправляется на страницу поста, к которому относится комментарий.
    """

    pass


class ProfileDetailView(ListView):
    """
    Страница профиля пользователя.

    Отображает список постов пользователя с пагинацией (10 постов на страницу),
    аннотируя количество комментариев и сортируя по убыванию даты публикации.

    Для автора отображаются все его посты,
    для остальных — только опубликованные.
    """

    template_name = 'blog/profile.html'
    paginate_by = PAGINATE_BY

    def dispatch(self, request, *args, **kwargs):
        self.profile = get_object_or_404(User, username=kwargs['username'])
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return post_set_processing(
            self.profile.posts.all(),
            apply_filtering=self.request.user != self.profile,
            select_related_fields=['author', 'category'],
            annotate_comment_count=True
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            **kwargs,
            profile=self.profile
        )


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """
    Страница редактирования профиля пользователя.

    Доступна только авторизованному пользователю для редактирования
    собственного профиля. После редактирования пользователь перенаправляется
    на страницу своего профиля.
    """

    model = User
    form_class = UserUpdateForm
    template_name = 'blog/user.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse(
            'blog:profile', args=[self.request.user.username]
        )
