from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('tanks/', views.TankListView.as_view(), name='tank_list'),
    path('tanks/<uuid:pk>/', views.TankDetailView.as_view(), name='tank_detail'),
    path('tanks/<uuid:tank_id>/data/', views.tank_data_api, name='tank_data_api'),
    path('tanks/<uuid:tank_id>/export/', views.export_tank_data, name='export_tank_data'),
    path('tanks/<uuid:tank_id>/chart-data/', views.tank_chart_data_api, name='tank_chart_data_api'),
    path('alerts/', views.alerts_view, name='alerts'),
    path('api/dashboard-data/', views.dashboard_data_api, name='dashboard_data_api'),
] 