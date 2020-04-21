from django.urls import path
from .views import *

urlpatterns = [
    path('test', return_404, name="return_404")
]
