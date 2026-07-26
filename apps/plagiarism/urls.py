from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('initialize/', views.initialize_view, name='initialize'),
]
