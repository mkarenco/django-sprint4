"""Конфигурация URL-маршрутов приложения.

Этот модуль определяет маршруты для административной панели,
статических страниц,блога, аутентификации, регистрации и обработки медиафайлов.
"""

from blog.views import CustomLogoutView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.urls import include, path, reverse_lazy
from django.views.generic.edit import CreateView

# Обработчики ошибок
handler500 = 'pages.views.server_error'
handler404 = 'pages.views.page_not_found'
handler403 = 'pages.views.csrf_failure'

# Основные маршруты приложения
urlpatterns = [
    # Административная панель
    path('admin/', admin.site.urls),
    # Статические страницы
    path('pages/', include('pages.urls', namespace='pages')),
    # Выход из системы
    path('auth/logout/', CustomLogoutView.as_view(), name='logout'),
    # Встроенные маршруты аутентификации Django
    path('auth/', include('django.contrib.auth.urls')),
    # Регистрация нового пользователя
    path(
        'auth/registration/',
        CreateView.as_view(
            template_name='registration/registration_form.html',
            form_class=UserCreationForm,
            success_url=reverse_lazy('blog:index'),
        ),
        name='registration',
    ),
    # Маршруты блога (главная страница)
    path('', include('blog.urls', namespace='blog')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
