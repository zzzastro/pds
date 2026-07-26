from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('initialize/', views.initialize_view, name='initialize'),
    path('dataset-preview/', views.dataset_preview, name='dataset_preview'),
    path('dataset-download/', views.download_dataset, name='dataset_download'),
]
