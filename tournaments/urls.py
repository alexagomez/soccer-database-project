from django.urls import path
from .views import *

urlpatterns = [
    path('view', view_tournaments, name="view_tournaments"),
    path('edit', edit_tournament, name="edit_tournament"),
    path('add', add_tournament, name="add_tournament")
]
