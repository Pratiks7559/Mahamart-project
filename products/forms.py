from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Product, Category


class ProductForm(forms.ModelForm):
    """Form for creating and editing products"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = False

    class Meta:
        model = Product
        fields = [
            'category', 'name', 'slug', 'sku', 'description', 
            'price', 'discount_type', 'discount_value', 'stock', 'main_image', 
            'is_featured', 'is_active'
        ]
        widgets = {
            'category': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter product name'}),
            'slug': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Auto-generated from name'}),
            'sku': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g., PROD-1001'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5, 'placeholder': 'Enter product description'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
            'discount_type': forms.Select(attrs={'class': 'form-input'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'main_image': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
        labels = {
            'category': 'Category',
            'name': 'Product Name',
            'slug': 'URL Slug',
            'sku': 'SKU (Stock Keeping Unit)',
            'description': 'Description',
            'price': 'Regular Price',
            'discount_type': 'Discount Type',
            'discount_value': 'Discount Value',
            'stock': 'Stock Quantity',
            'main_image': 'Product Image',
            'is_featured': 'Feature this product',
            'is_active': 'Active (visible on site)',
        }
        help_texts = {
            'slug': 'Leave blank to auto-generate from name',
            'discount_value': 'Flat is an amount in rupees; Percentage is a value below 100.',
            'stock': 'Quantity available in inventory',
        }
    
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if sku:
            # Check if SKU already exists (exclude current instance for edit)
            instance = getattr(self, 'instance', None)
            if instance and instance.pk:
                if Product.objects.filter(sku=sku).exclude(pk=instance.pk).exists():
                    raise ValidationError('A product with this SKU already exists.')
            else:
                if Product.objects.filter(sku=sku).exists():
                    raise ValidationError('A product with this SKU already exists.')
        return sku

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['discount_type'] = cleaned_data.get('discount_type') or Product.DiscountType.FLAT
        return cleaned_data


class VendorProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['category', 'name', 'description', 'price', 'discount_type', 'discount_value', 'stock', 'main_image']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-input'}),
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
            'discount_type': forms.Select(attrs={'class': 'form-input'}),
            'discount_value': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01', 'min': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input', 'min': '0'}),
            'main_image': forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        }
        labels = {
            'price': 'Your selling price',
            'main_image': 'Product image',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['name'].required = True
        self.fields['price'].required = True
        self.fields['discount_type'].required = False

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['discount_type'] = cleaned_data.get('discount_type') or Product.DiscountType.FLAT
        return cleaned_data


class VendorProductReviewForm(forms.Form):
    margin = forms.DecimalField(
        min_value=Decimal('0.00'),
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'class': 'form-input'}),
    )
    action = forms.ChoiceField(choices=[('approve', 'Approve'), ('reject', 'Reject')])