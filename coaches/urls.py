from django.urls import path
from .views import *

urlpatterns = [
    path('view', view_coaches, name="view_coaches"),
    path('edit', edit_coach, name="edit_coach"),
    path('add', add_coach, name="add_coach")
]
