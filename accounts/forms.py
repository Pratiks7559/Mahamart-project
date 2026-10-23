from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
import re
from .models import User, VendorApplication
from products.models import Category


class UserRegistrationForm(UserCreationForm):
    full_name = forms.CharField(
        max_length=100, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your full name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter your email'})
    )
    phone = forms.CharField(
        max_length=15, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your mobile number'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-input', 'rows': 3, 'placeholder': 'Enter your address'}),
        required=False
    )
    
    class Meta:
        model = User
        fields = ['username', 'full_name', 'email', 'phone', 'address', 'password1', 'password2']
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exists():
            raise ValidationError('This phone number is already registered.')
        return phone
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.full_name = self.cleaned_data.get('full_name')
        user.email = self.cleaned_data.get('email')
        user.phone = self.cleaned_data.get('phone')
        user.address = self.cleaned_data.get('address', '')
        user.is_phone_verified = False
        
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your mobile number'})
    )
    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Enter your password'})
    )


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone', 'address', 'profile_picture']
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if User.objects.filter(phone=phone).exclude(id=self.instance.id).exists():
            raise ValidationError('This phone number is already in use.')
        return phone


class VendorApplicationForm(forms.ModelForm):
    categories = forms.ModelMultipleChoiceField(
        queryset=Category.objects.filter(is_active=True),
        widget=forms.SelectMultiple(attrs={'class': 'form-input', 'size': 5}),
        required=True,
    )
    products_by_category = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-input',
            'rows': 5,
            'placeholder': 'One category: rice, flour. Multiple categories: Grocery: rice, Clothing: shirts.',
        }),
        help_text='For one category, enter comma-separated products. For multiple categories, enter one line per category as Category: product 1, product 2.',
    )
    phone = forms.CharField(
        max_length=20,
        validators=[RegexValidator(r'^\+?[\d\s()-]{10,20}$', 'Enter a valid mobile number (10 to 15 digits).')],
    )
    gst_number = forms.CharField(
        max_length=15,
        validators=[RegexValidator(
            r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$',
            'Enter a valid 15-character GST number.',
            flags=re.IGNORECASE,
        )],
    )
    pan_number = forms.CharField(
        max_length=10,
        validators=[RegexValidator(
            r'^[A-Z]{5}[0-9]{4}[A-Z]$',
            'Enter a valid PAN number.',
            flags=re.IGNORECASE,
        )],
    )
    aadhaar_number = forms.CharField(
        max_length=20,
        validators=[RegexValidator(r'^[\d\s-]{12,20}$', 'Aadhaar number must contain 12 digits.')],
    )

    class Meta:
        model = VendorApplication
        fields = [
            'full_name', 'email', 'address', 'shop_name', 'registration_number',
            'gst_number', 'categories', 'shop_photo', 'phone', 'pan_number',
            'aadhaar_number',
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
            'shop_name': forms.TextInput(attrs={'class': 'form-input'}),
            'registration_number': forms.TextInput(attrs={'class': 'form-input'}),
            'shop_photo': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.applicant = user if getattr(user, 'is_authenticated', False) else None
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        existing_users = User.objects.filter(email__iexact=email)
        if self.applicant:
            existing_users = existing_users.exclude(pk=self.applicant.pk)
        if existing_users.exists():
            raise ValidationError('An account already uses this email address.')
        if VendorApplication.objects.filter(email__iexact=email, status=VendorApplication.Status.PENDING).exists():
            raise ValidationError('An application with this email is already pending.')
        return email

    def clean_phone(self):
        phone = re.sub(r'[\s()-]', '', self.cleaned_data['phone'])
        if not re.fullmatch(r'\+?\d{10,15}', phone):
            raise ValidationError('Enter a valid mobile number (10 to 15 digits).')
        existing_users = User.objects.filter(phone=phone)
        if self.applicant:
            existing_users = existing_users.exclude(pk=self.applicant.pk)
        if existing_users.exists():
            raise ValidationError('An account already uses this mobile number.')
        return phone

    def clean_gst_number(self):
        return self.cleaned_data['gst_number'].strip().upper()

    def clean_pan_number(self):
        return self.cleaned_data['pan_number'].strip().upper()

    def clean_aadhaar_number(self):
        aadhaar = re.sub(r'[\s-]', '', self.cleaned_data['aadhaar_number'])
        if not re.fullmatch(r'\d{12}', aadhaar):
            raise ValidationError('Aadhaar number must contain 12 digits.')
        return aadhaar

    def clean_products_by_category(self):
        raw_value = self.cleaned_data['products_by_category']
        selected_categories = {category.name.casefold(): category for category in self.cleaned_data.get('categories', [])}
        products = {}
        if len(selected_categories) == 1 and ':' not in raw_value:
            category = next(iter(selected_categories.values()))
            names = [name.strip() for name in re.split(r'[,\n]', raw_value) if name.strip()]
            if names:
                return {category.name: names}
        for line in raw_value.splitlines():
            category_name, separator, product_names = line.partition(':')
            category = selected_categories.get(category_name.strip().casefold())
            names = [name.strip() for name in product_names.split(',') if name.strip()]
            if not separator or not category or not names:
                raise ValidationError('Use one line per selected category: Category: product 1, product 2.')
            products[category.name] = names
        if set(products) != {category.name for category in selected_categories.values()}:
            raise ValidationError('Provide a product list for every selected category.')
        return products