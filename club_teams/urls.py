from django.urls import path
from .views import *

urlpatterns = [
    path('view', view_club_teams, name="view_club_teams"),
    path('edit', edit_club_team, name="edit_club_team"),
    path('add', add_club_team, name="add_club_team")
]
