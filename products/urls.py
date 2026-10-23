from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Public URLs
    path('about/', views.about, name='about'),
    path('help/', views.help_center, name='help_center'),
    path('shop/', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.category_products, name='category_products'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    
    # Cart & Search
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('search/', views.search_products, name='search_products'),
    
    # Custom Admin URLs - ADD THESE WITH CORRECT NAMES
    path('admin/products/', views.product_list_admin, name='product_list_admin'),
    path('admin/products/add/', views.product_add, name='product_add'),
    path('admin/products/edit/<int:product_id>/', views.product_edit, name='product_edit'),
    path('admin/products/delete/<int:product_id>/', views.product_delete, name='product_delete'),
    path('admin/category/add/', views.category_add_ajax, name='category_add_ajax'),
]