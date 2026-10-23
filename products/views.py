from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.text import slugify
from django.db.models import Q, Count
from django.http import JsonResponse  # ADD THIS LINE
from .models import Product, Category
from .forms import ProductForm, VendorProductForm


# ============================================
# PUBLIC VIEWS
# ============================================

def home(request):
    """
    Homepage with hero section, search, and trending products
    """
    # Get featured/trending products
    trending_products = Product.objects.filter(
        is_active=True,
        is_featured=True,
        review_status=Product.ReviewStatus.APPROVED,
    ).select_related('category')[:12]
    
    # If no featured products, get latest products
    if not trending_products:
        trending_products = Product.objects.filter(
            is_active=True,
            review_status=Product.ReviewStatus.APPROVED,
        ).select_related('category').order_by('-created_at')[:12]
    
    # Get categories for navbar
    categories = Category.objects.filter(is_active=True)
    
    # Get top selling (by stock - placeholder logic)
    top_selling = Product.objects.filter(
        is_active=True,
        review_status=Product.ReviewStatus.APPROVED,
    ).order_by('-stock')[:6]
    
    context = {
        'trending_products': trending_products,
        'categories': categories,
        'top_selling': top_selling,
        'page_title': 'Welcome to Product Store',
        'user': request.user,
    }
    return render(request, 'home.html', context)


def about(request):
    featured_products = Product.objects.filter(
        is_active=True,
        review_status=Product.ReviewStatus.APPROVED,
        main_image__isnull=False,
    ).exclude(main_image='').select_related('category')[:3]
    return render(request, 'pages/about.html', {
        'featured_products': featured_products,
        'page_title': 'About Us',
    })


def help_center(request):
    return render(request, 'pages/help.html', {
        'page_title': 'Help Center',
    })


def product_list(request):
    """
    Display all active products with search
    """
    products = Product.objects.filter(
        is_active=True,
        review_status=Product.ReviewStatus.APPROVED,
    ).select_related('category')
    
    search_query = request.GET.get('q', '').strip()
    
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query) |
            Q(sku__icontains=search_query)
        )
    
    context = {
        'products': products,
        'page_title': 'Shop - All Products',
        'search_query': search_query,
        'total_products': products.count(),
        'user': request.user,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    """
    Display detailed information for a single product
    """
    product = get_object_or_404(
        Product.objects.select_related('category'),
        slug=slug,
        is_active=True,
        review_status=Product.ReviewStatus.APPROVED,
    )
    
    # Get related products from same category
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        review_status=Product.ReviewStatus.APPROVED,
    ).exclude(id=product.id)[:8]
    
    context = {
        'product': product,
        'related_products': related_products,
        'page_title': f'{product.name} - Product Details',
        'user': request.user,
    }
    return render(request, 'products/product_detail.html', context)


def category_products(request, slug):
    """
    Display all active products in a specific category
    """
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(
        category=category,
        is_active=True,
        review_status=Product.ReviewStatus.APPROVED,
    )
    
    context = {
        'category': category,
        'products': products,
        'page_title': f'{category.name} - Products',
        'total_products': products.count(),
        'user': request.user,
    }
    return render(request, 'products/category_products.html', context)


@login_required
def add_to_cart(request):
    """
    Add product to cart (placeholder - will be implemented later)
    """
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        # Check if product exists
        product = get_object_or_404(
            Product,
            id=product_id,
            is_active=True,
            review_status=Product.ReviewStatus.APPROVED,
        )
        
        # Placeholder for cart functionality
        messages.success(request, f'{product.name} added to cart!')
        return redirect('products:product_detail', slug=product.slug)
    
    return redirect('products:product_list')


def search_products(request):
    """
    AJAX search for products
    """
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query),
            is_active=True,
            review_status=Product.ReviewStatus.APPROVED,
        )[:10]
        
        results = []
        for product in products:
            results.append({
                'id': product.id,
                'name': product.name,
                'price': str(product.final_price),
                'slug': product.slug,
                'image': product.main_image.url if product.main_image else None,
                'discount': product.discount_percentage,
            })
        
        return JsonResponse({'results': results})
    
    return JsonResponse({'results': []})


# ============================================
# ADMIN VIEWS (Custom - No Django Admin)
# ============================================

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_superuser


@login_required
@user_passes_test(is_admin)
def product_add(request):
    """
    Custom page for adding a new product
    """
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # Auto-generate slug if not provided
            if not product.slug:
                product.slug = slugify(product.name)
            product.save()
            messages.success(request, f'Product "{product.name}" has been created successfully!')
            return redirect('products:product_edit', product_id=product.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'categories': categories,
        'page_title': 'Add New Product',
        'is_edit': False,
    }
    return render(request, 'products/product_form.html', context)


@login_required
@user_passes_test(is_admin)
def product_edit(request, product_id):
    """
    Custom page for editing an existing product
    """
    product = get_object_or_404(Product, id=product_id)
    categories = Category.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            # Auto-generate slug if not provided
            if not product.slug:
                product.slug = slugify(product.name)
            product.save()
            messages.success(request, f'Product "{product.name}" has been updated successfully!')
            return redirect('products:product_edit', product_id=product.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm(instance=product)
    
    context = {
        'form': form,
        'product': product,
        'categories': categories,
        'page_title': f'Edit Product - {product.name}',
        'is_edit': True,
    }
    return render(request, 'products/product_form.html', context)


@login_required
@user_passes_test(is_admin)
def product_delete(request, product_id):
    """
    Delete a product
    """
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" has been deleted successfully!')
        return redirect('products:product_list')
    
    context = {
        'product': product,
        'page_title': f'Delete Product - {product.name}',
    }
    return render(request, 'products/product_confirm_delete.html', context)


@login_required
@user_passes_test(is_admin)
def category_add_ajax(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            return JsonResponse({'success': False, 'error': 'Category name is required.'})
        if Category.objects.filter(name__iexact=name).exists():
            return JsonResponse({'success': False, 'error': 'Category already exists.'})
        category = Category.objects.create(
            name=name,
            slug=slugify(name),
            is_active=True
        )
        return JsonResponse({'success': True, 'id': category.id, 'name': category.name})
    return JsonResponse({'success': False, 'error': 'Invalid request.'})


@login_required
@user_passes_test(is_admin)
def product_list_admin(request):
    """
    Admin view for managing all products
    """
    products = Product.objects.all().select_related('category').order_by('-created_at')
    
    context = {
        'products': products,
        'page_title': 'Manage Products',
    }
    return render(request, 'products/product_list_admin.html', context)


@login_required(login_url='accounts:vendor_login')
def vendor_product_add(request):
    if not request.user.is_vendor:
        return redirect('home')

    if request.method == 'POST':
        form = VendorProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user
            product.review_status = Product.ReviewStatus.PENDING
            product.is_active = False
            product.save()
            messages.success(request, 'Product submitted. It will appear in the store after admin approval.')
            return redirect('accounts:vendor_portal')
    else:
        form = VendorProductForm()

    return render(request, 'products/vendor_product_form.html', {'form': form})