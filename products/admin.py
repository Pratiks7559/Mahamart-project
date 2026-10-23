from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Category, Product, ProductImage


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'product_count', 'created_at']
    search_fields = ['name', 'slug', 'description']
    list_filter = ['is_active', 'created_at']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['name']

    def product_count(self, obj):
        """Count products in this category"""
        count = obj.products.filter(is_active=True).count()
        return format_html(
            '<span style="font-weight: bold; color: #417690;">{}</span>',
            count
        )
    product_count.short_description = 'Active Products'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(total_products=Count('products'))


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name',
        'sku',
        'category',
        'price_display',
        'stock_display',
        'is_active',
        'created_at'
    ]
    search_fields = ['name', 'slug', 'sku', 'description']
    list_filter = ['category', 'is_active', 'created_at']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    # Simplified fieldsets - removed the problematic description
    fieldsets = (
        ('Basic Information', {
            'fields': ('category', 'name', 'slug', 'sku', 'description')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_type', 'discount_value')
        }),
        ('Inventory', {
            'fields': ('stock',)
        }),
        ('Media', {
            'fields': ('main_image',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def price_display(self, obj):
        """Display price with discount if applicable"""
        if obj.discount_value is not None:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">₹{}</span> '
                '<span style="color: #c62828; font-weight: bold;">₹{}</span> '
                '<span style="color: #2e7d32;">(-{}%)</span>',
                obj.customer_price,
                obj.customer_discount_price,
                obj.discount_percentage
            )
        return format_html('<span style="font-weight: bold;">₹{}</span>', obj.customer_price)
    price_display.short_description = 'Price'

    def stock_display(self, obj):
        """Display stock with color coding"""
        if obj.stock > 10:
            color = '#2e7d32'
            status = 'In Stock'
        elif obj.stock > 0:
            color = '#ed6c02'
            status = 'Low Stock'
        else:
            color = '#d32f2f'
            status = 'Out of Stock'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} ({})</span>',
            color,
            obj.stock,
            status
        )
    stock_display.short_description = 'Stock'

    def save_model(self, request, obj, form, change):
        """Override to ensure validation before saving"""
        obj.clean()
        super().save_model(request, obj, form, change)


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    list_filter = ['is_primary', 'created_at', 'product']
    list_editable = ['is_primary']
    readonly_fields = ['created_at']
    list_per_page = 25

    def image_preview(self, obj):
        """Show image thumbnail in admin"""
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 50px; max-width: 50px; border-radius: 4px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'Preview'

    fieldsets = (
        ('Product & Image', {
            'fields': ('product', 'image', 'alt_text')
        }),
        ('Display Settings', {
            'fields': ('is_primary',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )