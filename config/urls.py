from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from admin_dashboard import views as admin_dashboard_views
from products.views import home

urlpatterns = [
    path('', home, name='home'),
    # Main app URLs - products.urls now handles everything
    path('', include('products.urls')),  # This includes all product URLs including admin
    path('admin-login', admin_dashboard_views.admin_login, name='admin_login_shortcut'),
    path('admin-login/', admin_dashboard_views.admin_login, name='admin_login_shortcut_slash'),
    path('accounts/', include('accounts.urls')),
    path('admin-dashboard/', include('admin_dashboard.urls')),
    
    # Built-in Django admin (keep this for other models)
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)