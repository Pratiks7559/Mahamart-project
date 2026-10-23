from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Count, Sum
from products.models import Category, Product
from accounts.models import User as CustomUser
from django.utils import timezone
from datetime import timedelta
import smtplib
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import IntegrityError, transaction
from django.views.decorators.http import require_POST
from accounts.models import VendorApplication
from products.forms import VendorProductReviewForm


def is_admin(user):
    """Check if user is superuser/admin"""
    return user.is_authenticated and user.is_superuser


def admin_login(request):
    """Admin login page"""
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_superuser:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('admin_dashboard:dashboard')
        elif user is not None and not user.is_superuser:
            messages.error(request, 'You do not have admin privileges.')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'admin_dashboard/admin_login.html')


@login_required
@user_passes_test(is_admin)
@require_POST
def admin_logout(request):
    """Admin logout"""
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('admin_dashboard:admin_login')


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """Admin dashboard with statistics"""
    # Get statistics
    total_products = Product.objects.filter(is_active=True).count()
    total_categories = Category.objects.filter(is_active=True).count()
    total_users = CustomUser.objects.count()
    total_orders = 0  # Will be added later
    
    # Recent products
    recent_products = Product.objects.filter(is_active=True).order_by('-created_at')[:5]
    
    # Low stock products
    low_stock_products = Product.objects.filter(is_active=True, stock__lte=10).order_by('stock')[:5]
    
    # Categories with product count
    categories_with_count = Category.objects.filter(is_active=True).annotate(
        product_count=Count('products')
    ).order_by('-product_count')[:5]
    
    context = {
        'total_products': total_products,
        'total_categories': total_categories,
        'total_users': total_users,
        'total_orders': total_orders,
        'recent_products': recent_products,
        'low_stock_products': low_stock_products,
        'categories_with_count': categories_with_count,
        'page_title': 'Admin Dashboard',
        'user': request.user,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_profile(request):
    """Admin profile page"""
    if request.method == 'POST':
        # Update profile
        user = request.user
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if email:
            user.email = email
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('admin_dashboard:admin_profile')
    
    return render(request, 'admin_dashboard/admin_profile.html', {'user': request.user})


@login_required
@user_passes_test(is_admin)
def manage_users(request):
    """Manage users (admin only)"""
    users = CustomUser.objects.all().order_by('-date_joined')
    return render(request, 'admin_dashboard/manage_users.html', {'users': users})


@login_required
@user_passes_test(is_admin)
def manage_products(request):
    """Manage products (admin only)"""
    products = Product.objects.all().select_related('category').order_by('-created_at')
    return render(request, 'admin_dashboard/manage_products.html', {'products': products})


@login_required
@user_passes_test(is_admin)
def manage_vendor_products(request):
    products = Product.objects.filter(vendor__isnull=False).select_related(
        'vendor', 'category'
    ).order_by('review_status', '-created_at')
    return render(request, 'admin_dashboard/vendor_products.html', {
        'pending_products': products.filter(review_status=Product.ReviewStatus.PENDING),
        'reviewed_products': products.exclude(review_status=Product.ReviewStatus.PENDING),
    })


@login_required
@user_passes_test(is_admin)
def review_vendor_product(request, product_id):
    if request.method != 'POST':
        return redirect('admin_dashboard:manage_vendor_products')

    product = get_object_or_404(
        Product,
        pk=product_id,
        vendor__isnull=False,
        review_status=Product.ReviewStatus.PENDING,
    )
    form = VendorProductReviewForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'Enter a valid margin of zero or more.')
        return redirect('admin_dashboard:manage_vendor_products')

    product.admin_margin = form.cleaned_data['margin']
    if form.cleaned_data['action'] == 'approve':
        product.review_status = Product.ReviewStatus.APPROVED
        product.is_active = True
        message = f'{product.name} approved and added to the store.'
    else:
        product.review_status = Product.ReviewStatus.REJECTED
        product.is_active = False
        message = f'{product.name} rejected.'
    product.save(update_fields=['admin_margin', 'review_status', 'is_active', 'updated_at'])
    messages.success(request, message)
    return redirect('admin_dashboard:manage_vendor_products')


@login_required
@user_passes_test(is_admin)
def manage_vendors(request):
    applications = VendorApplication.objects.all()
    return render(request, 'admin_dashboard/manage_vendors.html', {
        'total_applications': applications.count(),
        'pending_count': applications.filter(status=VendorApplication.Status.PENDING).count(),
        'approved_count': applications.filter(status=VendorApplication.Status.APPROVED).count(),
        'rejected_count': applications.filter(status=VendorApplication.Status.REJECTED).count(),
    })


@login_required
@user_passes_test(is_admin)
def vendor_applications_by_status(request, status):
    sections = {
        VendorApplication.Status.PENDING: ('Pending applications', 'NEEDS REVIEW'),
        VendorApplication.Status.APPROVED: ('Approved applications', 'ACTIVE PARTNERS'),
        VendorApplication.Status.REJECTED: ('Rejected applications', 'CLOSED'),
    }
    title, eyebrow = sections[status]
    applications = VendorApplication.objects.filter(status=status)
    return render(request, 'admin_dashboard/vendor_application_list.html', {
        'applications': applications,
        'title': title,
        'eyebrow': eyebrow,
    })


@login_required
@user_passes_test(is_admin)
def vendor_application_detail(request, application_id):
    application = get_object_or_404(
        VendorApplication.objects.prefetch_related('categories'),
        pk=application_id,
    )
    return render(request, 'admin_dashboard/vendor_application_detail.html', {
        'application': application,
    })


@login_required
@user_passes_test(is_admin)
def approve_vendor(request, application_id):
    if request.method != 'POST':
        return redirect('admin_dashboard:manage_vendors')

    try:
        application = VendorApplication.objects.get(pk=application_id)
    except VendorApplication.DoesNotExist:
        messages.error(request, 'Vendor application not found.')
        return redirect('admin_dashboard:manage_vendors')

    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    vendor = application.applicant
    username_users = CustomUser.objects.filter(username=username)
    email_users = CustomUser.objects.filter(email__iexact=application.email)
    phone_users = CustomUser.objects.filter(phone=application.phone)
    if vendor:
        username_users = username_users.exclude(pk=vendor.pk)
        email_users = email_users.exclude(pk=vendor.pk)
        phone_users = phone_users.exclude(pk=vendor.pk)
    if application.status != VendorApplication.Status.PENDING:
        messages.error(request, 'Only pending applications can be approved.')
    elif not username or not password:
        messages.error(request, 'Enter a vendor login ID and password.')
    elif username_users.exists():
        messages.error(request, 'That login ID is already in use.')
    elif email_users.exists():
        messages.error(request, 'An account already uses this vendor email.')
    elif phone_users.exists():
        messages.error(request, 'An account already uses this vendor mobile number.')
    else:
        vendor = vendor or CustomUser()
        vendor.username = username
        vendor.email = application.email
        vendor.full_name = application.full_name
        vendor.phone = application.phone
        vendor.address = application.address
        vendor.is_vendor = True
        vendor.is_active = True
        try:
            validate_password(password, user=vendor)
            vendor.set_password(password)
            with transaction.atomic():
                vendor.save()
                sent = send_mail(
                    'Your Product Store vendor account',
                    f'Hello {application.full_name},\n\nYour vendor application for {application.shop_name} has been approved.\n\nLogin ID: {username}\nPassword: {password}\nVendor login: {request.build_absolute_uri("/accounts/vendor/login/")}\n\nPlease change your password after logging in.',
                    settings.DEFAULT_FROM_EMAIL,
                    [application.email],
                    fail_silently=False,
                )
                if not sent:
                    raise smtplib.SMTPException('Email backend did not send the message.')
                application.mark_reviewed(VendorApplication.Status.APPROVED)
            messages.success(request, f'Vendor approved. Login credentials were emailed to {application.email}.')
        except ValidationError as error:
            messages.error(request, 'Password: ' + ' '.join(error.messages))
        except (smtplib.SMTPException, OSError, IntegrityError):
            messages.error(request, 'Approval was not completed because the account email could not be sent. Check the SMTP settings and try again.')

    return redirect('admin_dashboard:manage_vendors')


@login_required
@user_passes_test(is_admin)
def reject_vendor(request, application_id):
    if request.method == 'POST':
        try:
            application = VendorApplication.objects.get(pk=application_id)
            if application.status == VendorApplication.Status.PENDING:
                application.mark_reviewed(VendorApplication.Status.REJECTED)
                messages.success(request, 'Vendor application rejected.')
            else:
                messages.error(request, 'Only pending applications can be rejected.')
        except VendorApplication.DoesNotExist:
            messages.error(request, 'Vendor application not found.')
    return redirect('admin_dashboard:manage_vendors')


@login_required
@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    if request.method == 'POST':
        try:
            user = CustomUser.objects.get(id=user_id)
            # Don't allow deactivating yourself
            if user.id == request.user.id:
                messages.error(request, 'You cannot deactivate yourself.')
                return redirect('admin_dashboard:manage_users')
            
            user.is_active = not user.is_active
            user.save()
            status = 'activated' if user.is_active else 'deactivated'
            messages.success(request, f'User {user.username} has been {status}.')
        except CustomUser.DoesNotExist:
            messages.error(request, 'User not found.')
    
    return redirect('admin_dashboard:manage_users')