from django.urls import path
from .views import *

urlpatterns = [
    path('view_club_teams', view_club_teams, name="view_club_teams"),
    path('view_national_teams', view_national_teams, name="view_national_teams")
]
