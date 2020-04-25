from django.urls import path
from .views import *

urlpatterns = [
    path('view', view_leagues, name="view_leagues"),
    path('edit', edit_league, name="edit_league"),
    path('add', add_league, name="add_league")
]
