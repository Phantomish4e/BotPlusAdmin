from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_incident_list, name='dashboard'),
    path('data', views.pivot_data, name='pivot-data')
]
