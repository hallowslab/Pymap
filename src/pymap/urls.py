"""
URL configuration for pymap project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.conf import settings

from migrator.admin import custom_admin_site

urlpatterns = [
    path("admin/doc/", include("django.contrib.admindocs.urls")),
    # path("admin/", admin.site.urls),
    path("admin/", custom_admin_site.urls, name="index"),
    path("", include("migrator.urls", namespace="migrator")),
    path(
        "login/",
        auth_views.LoginView.as_view(
            template_name="admin/login.html",
            success_url="/sync",
            redirect_authenticated_user=True,
        ),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="/"), name="logout"),
    path(
        "password-change/",
        login_required(auth_views.PasswordChangeView.as_view(success_url="/account")),
        name="password-change",
    ),
    path(
        "password-change-done/",
        login_required(auth_views.PasswordResetDoneView.as_view()),
        name="password-change-done",
    ),
] + ([path("__debug__/", include("debug_toolbar.urls"))] if settings.DEBUG else [])
