from django.urls import path
from . import views

urlpatterns = [
    path('reports/', views.report_list, name='report_list'),
    path('reports/generate/', views.report_generate, name='report_generate'),
    path('reports/save/', views.report_save, name='report_save'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/<int:pk>/edit/', views.report_edit, name='report_edit'),
]