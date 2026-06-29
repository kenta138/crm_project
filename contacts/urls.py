from django.urls import path
from . import views

urlpatterns = [
    path('contacts/', views.contact_list, name='contact_list'),
    path('contacts/new/', views.contact_new, name='contact_new'),
    path('contacts/<int:pk>/', views.contact_detail, name='contact_detail'),
    path('contacts/<int:pk>/edit/', views.contact_edit, name='contact_edit'),
    path('contacts/<int:pk>/delete/', views.contact_delete, name='contact_delete'),
]