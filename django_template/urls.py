from django.apps import apps
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from django_template.auth import urls as auth_urls

from . import views

api_urlpatterns = [
    path(
        "schema/",
        SpectacularAPIView.as_view(),
        name="schema",
    ),
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("auth/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/", include(auth_urls.api_urlpatterns)),
]

urlpatterns = [
    path("", include("django_template.core.urls")),
    path("api/", include(api_urlpatterns)),
    path("auth/", include("django.contrib.auth.urls")),
    path("registration/", include("django_template.registration.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    *i18n_patterns(path("django-admin/", admin.site.urls)),
    path("health/", views.health, name="health"),
    path("__internal__/meta/", views.meta, name="meta"),
    path("__internal__/simulate-403/", views.simulate_403, name="simulate-403"),
    path("__internal__/simulate-500/", views.simulate_500, name="simulate-500"),
    path("hijack/", include("hijack.urls")),
    path("silk/", include("silk.urls")),
]

if apps.is_installed("django_browser_reload"):
    urlpatterns.append(path("__reload__/", include("django_browser_reload.urls")))
