from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Admin Login/Logout
    path('login/', views.admin_login, name='admin_login'),
    path('logout/', views.admin_logout, name='admin_logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Profile
    path('profile/', views.admin_profile, name='admin_profile'),
    
    # Manage
    path('users/', views.manage_users, name='manage_users'),
    path('products/', views.manage_products, name='manage_products'),
    path('vendor-products/', views.manage_vendor_products, name='manage_vendor_products'),
    path('vendor-products/<int:product_id>/review/', views.review_vendor_product, name='review_vendor_product'),
    path('vendors/', views.manage_vendors, name='manage_vendors'),
    path('vendors/pending/', views.vendor_applications_by_status, {'status': 'pending'}, name='pending_vendors'),
    path('vendors/approved/', views.vendor_applications_by_status, {'status': 'approved'}, name='approved_vendors'),
    path('vendors/rejected/', views.vendor_applications_by_status, {'status': 'rejected'}, name='rejected_vendors'),
    path('vendors/<int:application_id>/', views.vendor_application_detail, name='vendor_application_detail'),
    path('vendors/<int:application_id>/approve/', views.approve_vendor, name='approve_vendor'),
    path('vendors/<int:application_id>/reject/', views.reject_vendor, name='reject_vendor'),
    path('users/toggle/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
]