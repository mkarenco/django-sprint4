"""
URL-маршруты для блог-приложения.

Этот модуль определяет маршруты для работы с главной страницей, постами,
комментариями, категориями и профилями пользователей. Маршруты сгруппированы
по функциональности для удобства чтения и поддержки кода.
"""

from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    # Маршрут для категорий
    path(
        'category/<slug:category_slug>/',
        views.CategoryPostsView.as_view(),
        name='category_posts',
    ),
    # Маршруты для постов
    path(
        'posts/<post_id>/edit_comment/<int:comment_id>/',
        views.CommentUpdateView.as_view(),
        name='edit_comment'
    ),
    path(
        'posts/<post_id>/delete_comment/<int:comment_id>/',
        views.CommentDeleteView.as_view(),
        name='delete_comment'
    ),
    path(
        'posts/<int:post_id>/delete/',
        views.PostDeleteView.as_view(),
        name='delete_post'
    ),
    path(
        'posts/<int:post_id>/edit/',
        views.PostUpdateView.as_view(),
        name='edit_post',
    ),
    path(
        'posts/<int:post_id>/comment/',
        views.CommentCreateView.as_view(),
        name='add_comment',
    ),
    path(
        'posts/<int:post_id>/',
        views.PostDetailView.as_view(),
        name='post_detail',
    ),
    path(
        'posts/create/',
        views.PostCreateView.as_view(),
        name='create_post'
    ),
    # Маршруты для профиля
    path(
        'profile/edit/',
        views.ProfileUpdateView.as_view(),
        name='edit_profile',
    ),
    path(
        'profile/<username>/',
        views.ProfileDetailView.as_view(),
        name='profile',
    ),
    # Главная страница
    path(
        '',
        views.HomePageListView.as_view(),
        name='index',
    ),
]
