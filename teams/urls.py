from django.urls import path
from .views import *

urlpatterns = [
    path('add_club_team', add_club_team, name="add_club_team"),
    path('add_national_team', add_national_team, name="add_national_team"),
    path('edit_club_team', edit_club_team, name="edit_club_team"),
    path('edit_national_team', edit_national_team, name="edit_national_team"),
    path('delete_club_team', delete_club_team, name="delete_club_team"),
    path('delete_national_team', delete_national_team, name="delete_national_team"),
    path('favorite/<str:long_name>', add_favorite_team, name="add_favorite_team"),
    path('view_club_teams', view_club_teams, name="view_club_teams"),
    path('view_national_teams', view_national_teams, name="view_national_teams")
]
