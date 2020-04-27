from django.urls import path
from .views import *

urlpatterns = [
    path('view', view_favorite_players, name="view_favorite_players"),
    path('unregistered', unregistered, name="unregistered"),
    path('delete/<str:player_name>', delete_favorite_players, name="delete_favorite")
]
