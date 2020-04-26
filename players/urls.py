from django.urls import path
from .views import *

urlpatterns = [
    path('view', view_players, name="view_players"),
    path('view_individual', view_individual, name="view_individual"),
    path('edit', edit_player, name="edit_player"),
    path('delete', delete_player, name="delete_player"),
    path('add', add_player, name="add_player"),
    path('favorite/<str:long_name>', add_favorite_player, name="add_favorite")
]
