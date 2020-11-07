from django.urls import path
from . import views

urlpatterns = [
    path('<summonerName>/search', views.search, name='index')
]