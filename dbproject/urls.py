"""dbproject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.urls import path, include
from users.views import SignUp
from django.conf.urls.static import static
from django.conf import settings
from users.views import login

urlpatterns = [
    path('admin/', admin.site.urls),
    path('club_teams/', include('club_teams.urls')),
    path('coaches/', include('coaches.urls')),
    path('players/', include('players.urls')),
    path('users/', include('users.urls')),
    path("", login, name="login"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
