from django.contrib import admin
from django.urls import path, include
from users.views import SignUp, LogIn, login, logout

urlpatterns = [
    path('signup', SignUp.as_view(), name="signup"),
    path('loginform', LogIn.as_view(), name="loginform"),
    path('logout', logout, name="logout"),
    path('login', login, name="login"),
]