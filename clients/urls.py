from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('clients/', views.client_list, name='client_list'),
    path('clients/new/', views.client_new, name='client_new'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/edit/', views.client_edit, name='client_edit'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    path('clients/import/', views.client_import, name='client_import'),
    path('clients/export/', views.client_export, name='client_export'),
    path('clients/import/template/', views.client_import_template, name='client_import_template'),
]