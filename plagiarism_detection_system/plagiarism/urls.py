from django.contrib.auth.views import LoginView
from django.urls import path, include
from .views import home, signup, login_view, logout_view, userprofile, delete_account
from django.conf import settings
from django.conf.urls.static import static  
from . import views
from django.contrib import admin

urlpatterns = [
    path('', home, name='home'),  # Home page
    path('signup/', views.signup, name='signup'),  # Signup page
    path('login/', views.login_view, name='login'),  # Login page
    path('userprofile/', userprofile, name='userprofile'),  # Profile page
    path('logout/', logout_view, name='logout'), #Logout
    path('delete_account/', delete_account, name='delete_account'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # Serve static files in debug mode