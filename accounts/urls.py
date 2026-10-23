from django.urls import path
from . import views
from products import views as product_views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('vendor/register/', views.vendor_register, name='vendor_register'),
    path('vendor/login/', views.vendor_login, name='vendor_login'),
    path('vendor/', views.vendor_portal, name='vendor_portal'),
    path('vendor/products/add/', product_views.vendor_product_add, name='vendor_product_add'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
]