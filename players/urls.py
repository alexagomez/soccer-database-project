from django.urls import path
from .views import *

urlpatterns = [
    path('view', view_players, name="view_players"),
    path('edit', edit_player, name="edit_player")
]
