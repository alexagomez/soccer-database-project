from django.urls import path
from .views import *

urlpatterns = [
    path('view', view_favorite_teams, name="view_favorite_teams"),
    path('delete/<str:team_name>', delete_favorite_team, name="delete_favorite")
]
