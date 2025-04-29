"""
Модуль с представлениями для статичных страниц проекта.

Содержит классы и функции для обработки запросов к страницам 'О проекте',
'Правила', а также обработчики ошибок 404, 403 (CSRF) и 500.
Каждое представление использует
соответствующий шаблон для отображения информации или ошибки на сайте.
"""

from django.shortcuts import render
from django.views.generic import TemplateView


class About(TemplateView):
    """
    Представление для страницы 'О проекте'.

    Обрабатывает запросы к странице с информацией о проекте, используя шаблон
    'pages/about.html' для отображения содержимого.
    """

    template_name = 'pages/about.html'


class Rules(TemplateView):
    """
    Представление для страницы 'Правила'.

    Обрабатывает запросы к странице с правилами проекта, используя шаблон
    'pages/rules.html' для отображения содержимого.
    """

    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    """Обработчик ошибки 404 (страница не найдена)."""
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason="", exception=None):
    """Обработчик ошибки 403 (CSRF-ошибка)."""
    return render(request, 'pages/403csrf.html', status=403)


def server_error(request):
    """Обработчик ошибки 500 (внутренняя ошибка сервера)."""
    return render(request, 'pages/500.html', status=500)
