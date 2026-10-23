from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from .models import User, VendorApplication
from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, VendorApplicationForm
from products.models import Product


def register(request):
    """
    User registration with full name, email, mobile, address
    """
    if request.user.is_authenticated:
        return redirect('home')  # Changed to 'home'
    
    if request.method == 'POST':
        print("=" * 50)
        print("REGISTRATION FORM SUBMITTED")
        print("POST data:", request.POST)
        print("=" * 50)
        
        form = UserRegistrationForm(request.POST, request.FILES)
        
        if form.is_valid():
            print("Form is VALID!")
            try:
                user = form.save(commit=False)
                user.full_name = form.cleaned_data['full_name']
                user.email = form.cleaned_data['email']
                user.phone = form.cleaned_data['phone']
                user.address = form.cleaned_data['address']
                user.save()
                print(f"User saved successfully: {user.username}")
                messages.success(request, f'Registration successful! Welcome {user.full_name}. Please login.')
                return redirect('accounts:login')
            except Exception as e:
                print(f"Error saving user: {e}")
                messages.error(request, f'Error creating account: {str(e)}')
        else:
            print("Form is INVALID!")
            print("Form errors:", form.errors)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    """
    User login with mobile number and password
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')

        try:
            user_obj = User.objects.get(phone=phone)
            user = authenticate(request, username=user_obj.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.full_name or user.username}!')
                return redirect('home')
            else:
                messages.error(request, 'Incorrect password. Please try again.')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this mobile number.')

    return render(request, 'accounts/login.html')


def vendor_register(request):
    form = VendorApplicationForm(request.POST or None, request.FILES or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        application = form.save(commit=False)
        if request.user.is_authenticated:
            application.applicant = request.user
        application.products_by_category = form.cleaned_data['products_by_category']
        application.save()
        form.save_m2m()
        messages.success(request, 'Form submitted successfully. Once your details are verified, the admin will email your vendor login credentials.')
        return redirect('/accounts/vendor/register/?submitted=1')

    return render(request, 'accounts/vendor_register.html', {
        'form': form,
        'submitted': request.GET.get('submitted') == '1',
    })


def vendor_login(request):
    if request.user.is_authenticated:
        return redirect('accounts:vendor_portal' if request.user.is_vendor else 'home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        account = User.objects.filter(username=username).first()
        if account is None or not account.check_password(password):
            messages.error(request, 'Invalid vendor login ID or password.')
        elif not account.is_active:
            messages.error(request, 'This vendor account is inactive. Please contact the admin to restore access.')
        elif not account.is_vendor:
            application = VendorApplication.objects.filter(
                Q(applicant=account) | Q(email__iexact=account.email)
            ).order_by('-submitted_at').first()
            if application and application.status == VendorApplication.Status.PENDING:
                messages.error(request, 'Your vendor application is still awaiting admin approval.')
            elif application and application.status == VendorApplication.Status.REJECTED:
                messages.error(request, 'Your vendor application was not approved. Please contact the admin for details.')
            else:
                messages.error(request, 'This account does not have vendor access. Please contact the admin.')
        else:
            user = authenticate(request, username=username, password=password)
            if user is None:
                messages.error(request, 'Unable to sign in with these vendor credentials. Please contact the admin.')
            else:
                login(request, user)
                return redirect('accounts:vendor_portal')

    return render(request, 'accounts/vendor_login.html')


@login_required(login_url='accounts:vendor_login')
def vendor_portal(request):
    if not request.user.is_vendor:
        return redirect('home')
    products = Product.objects.filter(vendor=request.user).select_related('category')
    live_products = Q(
        review_status=Product.ReviewStatus.APPROVED,
        is_active=True,
    )
    product_summary = products.aggregate(
        total=Count('pk'),
        live=Count('pk', filter=live_products),
        pending=Count('pk', filter=Q(review_status=Product.ReviewStatus.PENDING)),
        rejected=Count('pk', filter=Q(review_status=Product.ReviewStatus.REJECTED)),
        out_of_stock=Count('pk', filter=live_products & Q(stock=0)),
        low_stock=Count(
            'pk',
            filter=live_products & Q(stock__gt=0, stock__lte=5),
        ),
        live_stock_units=Sum('stock', filter=live_products),
    )
    low_stock_products = products.filter(
        live_products,
        stock__lte=5,
    ).order_by('stock', 'name')

    return render(request, 'accounts/vendor_portal.html', {
        'vendor': request.user,
        'products': products,
        'product_summary': product_summary,
        'low_stock_products': low_stock_products,
        'low_stock_limit': 5,
    })


def logout_view(request):
    """
    User logout
    """
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')  # Changed to 'home'


@login_required
def profile(request):
    """
    User profile page
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/profile.html', {'form': form, 'user': request.user})