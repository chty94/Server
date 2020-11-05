from django.urls import path
from . import views

urlpatterns = [
    path('<number>/', views.get, name='index')
]