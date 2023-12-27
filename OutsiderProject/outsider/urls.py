"""
URL configuration for 'outsider' project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

# Admin urls
# admin.site.site_url = "http://192.168.1.13:8080/"
admin.site.site_url = "http://192.168.0.16:8080/"
admin.site.site_header = "Django Administration - TFG"

# Swagger url configuration
schema_view = get_schema_view(
    openapi.Info(
        title="Swagger API - Outsider",
        default_version="v1.0",
        description="Swagger",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("logic/", include("logic.urls")),
    path("admin/", admin.site.urls),
]
