"""
Веб-представления для блог-приложения.

Этот модуль содержит классы представлений Django, реализующие функциональность
для работы с постами, категориями, комментариями, профилями пользователей и
выходом из системы. Используются миксины для фильтрации опубликованных постов
и ограничения доступа, а также generic views для упрощения обработки запросов.
"""

from django.contrib.auth import get_user_model, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import CommentForm, PostForm, UserUpdateForm
from .models import Category, Comment, Post

User = get_user_model()


class PublishedPostsMixin:
    """
    Миксин для фильтрации только опубликованных постов.

    Фильтрует посты по условиям: опубликован, дата публикации не позже текущего
    момента, категория опубликована. Использует select_related для оптимизации
    запросов к связанным таблицам (author, category).
    """

    def get_queryset(self):
        return super().get_queryset().select_related(
            'author',
            'category').filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        )


class OnlyAuthorMixin(UserPassesTestMixin):
    """
    Миксин для ограничения доступа к объекту только его автору.

    Проверяет, является ли текущий пользователь автором объекта. Используется
    для защиты операций редактирования и удаления постов и комментариев.
    """

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', post_id=self.kwargs['post_id'])


class HomePageListView(PublishedPostsMixin, ListView):
    """
    Главная страница с отсортированным списком опубликованных постов.

    Отображает список постов с пагинацией (10 постов на страницу), аннотируя
    количество комментариев и сортируя по убыванию даты публикации.
    """

    model = Post
    paginate_by = 10
    template_name = 'blog/index.html'

    def get_queryset(self):
        return (super().get_queryset()
                .annotate(comment_count=Count('comments'))
                .order_by('-pub_date'))


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
        """Получает пост и проверяет доступ для неопубликованных постов."""
        post = get_object_or_404(
            Post.objects.select_related('author', 'category', 'location'),
            pk=self.kwargs['post_id']
        )
        if post.author != self.request.user:
            return get_object_or_404(
                Post.objects.select_related('author', 'category', 'location'),
                pk=self.kwargs['post_id'],
                is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now())
        return post

    def get_context_data(self, **kwargs):
        """Добавляет форму комментариев и список комментариев в контекст."""
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.order_by('created_at')
        return context


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
            'blog:profile', kwargs={'username': self.request.user.username}
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
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})


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


class CategoryPostsView(PublishedPostsMixin, ListView):
    """
    Страница со списком постов по выбранной категории.

    Отображает только посты из опубликованной категории с пагинацией
    (10 постов на страницу). Категория определяется по slug из URL.
    """

    model = Post
    template_name = 'blog/category.html'
    context_object_name = 'post_list'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        queryset = super().get_queryset().filter(category=self.category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class CommentCreateView(LoginRequiredMixin, CreateView):
    """
    Страница создания комментария к посту.

    Доступна только авторизованным пользователям. После создания комментария
    пользователь перенаправляется на страницу поста.
    """

    model = Comment
    form_class = CommentForm

    def dispatch(self, request, *args, **kwargs):
        self.current_post = get_object_or_404(Post, pk=kwargs.get('post_id'))
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = self.current_post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.current_post.pk}
        )


class CommentUpdateView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    """
    Страница редактирования комментария.

    Доступна только автору комментария. После редактирования пользователь
    перенаправляется на страницу поста, к которому относится комментарий.
    """

    model = Comment
    form_class = CommentForm
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.object.post.pk}
        )


class CommentDeleteView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    """
    Страница удаления комментария.

    Доступна только автору комментария. После удаления пользователь
    перенаправляется на страницу поста, к которому относится комментарий.
    """

    model = Comment
    pk_url_kwarg = 'comment_id'
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse(
            'blog:post_detail', kwargs={'post_id': self.object.post.pk}
        )


class ProfileDetailView(ListView):
    """
    Страница профиля пользователя.

    Отображает список постов пользователя с пагинацией (10 постов на страницу),
    аннотируя количество комментариев и сортируя по убыванию даты публикации.
    """

    template_name = 'blog/profile.html'
    paginate_by = 10

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return Post.objects.filter(author=user).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context


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
            'blog:profile', kwargs={'username': self.request.user.username}
        )


class CustomLogoutView(View):
    """
    Кастомное представление для выхода пользователя из учетной записи.

    Обрабатывает GET-запрос для завершения сессии и отображает страницу
    подтверждения выхода.
    """

    template_name = 'registration/logged_out.html'

    def get(self, request, *args, **kwargs):
        """Обрабатывает GET-запрос для выхода из системы."""
        logout(request)
        return render(request, self.template_name)
