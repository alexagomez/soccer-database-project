from django.contrib import admin
from django.urls import path, include
from users.views import SignUp, LogIn, login, logout, RemoveAccount

urlpatterns = [
    path('signup', SignUp.as_view(), name="signup"),
    path('loginform', LogIn.as_view(), name="loginform"),
    path('logout', logout, name="logout"),
    path('remove', RemoveAccount.as_view(), name="remove"),
    path('login', login, name="login"),
]