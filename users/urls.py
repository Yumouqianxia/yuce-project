from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/change-username/', views.change_username, name='change_username'),
    path('profile/crop-avatar/', views.crop_avatar, name='crop_avatar'),
    path('profile/save-cropped-avatar/', views.save_cropped_avatar, name='save_cropped_avatar'),
    path('profile/upload-avatar/', views.upload_avatar, name='upload_avatar'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('', views.home, name='home'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('points/', views.points_detail, name='points_detail'),
    path('debug/points/', views.debug_points, name='debug_points'),
]
