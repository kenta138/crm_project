from django.urls import path
from . import views

urlpatterns = [
    path('labels/', views.label_top, name='label_top'),
    path('labels/category/new/', views.category_new, name='category_new'),
    path('labels/category/<int:pk>/edit/', views.category_edit, name='category_edit'),
    path('labels/category/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('labels/new/', views.label_new, name='label_new'),
    path('labels/<int:pk>/edit/', views.label_edit, name='label_edit'),
    path('labels/<int:pk>/delete/', views.label_delete, name='label_delete'),
    path('labels/<int:pk>/toggle/', views.label_toggle, name='label_toggle'),
]