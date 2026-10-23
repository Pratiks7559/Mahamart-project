from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'full_name', 'email', 'phone', 'is_active', 'is_superuser']
    search_fields = ['username', 'full_name', 'email', 'phone']
    list_filter = ['is_active', 'is_superuser', 'is_staff']
    
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('full_name', 'phone', 'address', 'profile_picture', 'is_phone_verified')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('full_name', 'phone', 'address', 'profile_picture', 'is_phone_verified')
        }),
    )