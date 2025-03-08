from django.urls import path
from . import views

urlpatterns = [
    path('', views.match_list, name='match_list'),
    path('finished/', views.finished_matches, name='finished_matches'),
    path('<int:match_id>/predict/', views.submit_prediction, name='predict_match'),
    path('admin/predictions/', views.admin_predictions, name='admin_predictions'),
    path('admin/check_consistency/', views.check_data_consistency, name='check_consistency'),
    path('my_predictions/', views.my_predictions, name='my_predictions'),
    path('admin/test_db/', views.test_db_connection, name='test_db_connection'),
] 