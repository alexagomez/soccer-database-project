from django.urls import path
from .views import *

urlpatterns = [
    path('test', view_players, name="view_players")
]
