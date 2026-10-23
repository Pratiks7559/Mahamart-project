from django.urls import path
from . import views

app_name = 'products_admin'

urlpatterns = [
    path('', views.product_list_admin, name='list'),
    path('add/', views.product_add, name='add'),
    path('edit/<int:product_id>/', views.product_edit, name='edit'),
    path('delete/<int:product_id>/', views.product_delete, name='delete'),
]