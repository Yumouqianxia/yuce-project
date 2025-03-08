from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('', views.home, name='home'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('points/', views.points_detail, name='points_detail'),
    path('debug/points/', views.debug_points, name='debug_points'),
]
