from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal


class Category(models.Model):
    """
    Category model for organizing products
    """
    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(max_length=120, unique=True, db_index=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to='categories/%Y/%m/',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:category_products', kwargs={'slug': self.slug})


class Product(models.Model):
    """
    Product model with pricing, inventory, and basic product information
    """
    class ReviewStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    class DiscountType(models.TextChoices):
        FLAT = 'flat', 'Flat amount'
        PERCENTAGE = 'percentage', 'Percentage'

    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name='Category'
    )
    name = models.CharField(max_length=200, db_index=True, blank=True, default='')
    slug = models.SlugField(max_length=220, unique=True, db_index=True, blank=True)
    sku = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        blank=True,
        null=True,
        verbose_name='SKU'
    )
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Price'
    )
    vendor = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
    )
    review_status = models.CharField(
        max_length=10,
        choices=ReviewStatus.choices,
        default=ReviewStatus.APPROVED,
        db_index=True,
    )
    admin_margin = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    discount_type = models.CharField(
        max_length=10,
        choices=DiscountType.choices,
        default=DiscountType.FLAT,
    )
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Discount Value'
    )
    stock = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name='Stock Quantity'
    )
    main_image = models.ImageField(
        upload_to='products/%Y/%m/',
        blank=True,
        null=True,
        verbose_name='Main Image'
    )
    is_featured = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        # Ensure slug uniqueness
        if Product.objects.filter(slug=self.slug).exclude(id=self.id).exists():
            self.slug = f"{self.slug}-{self.id or Product.objects.count() + 1}"
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Ensure the discount leaves a positive selling price."""
        if self.discount_value is None:
            return
        if self.price is None:
            raise ValidationError({
                'price': 'A regular price is required when a discount is set.'
            })
        if self.discount_type == self.DiscountType.PERCENTAGE:
            if self.discount_value <= 0 or self.discount_value >= 100:
                raise ValidationError({
                    'discount_value': 'Percentage discount must be greater than 0 and less than 100.'
                })
        elif self.discount_type == self.DiscountType.FLAT:
            if self.discount_value <= 0 or self.discount_value >= self.customer_price:
                raise ValidationError({
                    'discount_value': 'Flat discount must be greater than 0 and less than the regular price.'
                })

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock > 0

    @property
    def discount_percentage(self):
        """Calculate discount percentage if discount exists"""
        if self.discount_value is not None and self.customer_price > 0:
            discount = ((self.customer_price - self.customer_discount_price) / self.customer_price) * 100
            return round(discount, 0)
        return 0

    @property
    def customer_price(self):
        return (self.price or Decimal('0.00')) + self.admin_margin

    @property
    def customer_discount_price(self):
        if self.discount_value is None:
            return None
        if self.discount_type == self.DiscountType.PERCENTAGE:
            amount = self.customer_price * self.discount_value / Decimal('100')
        else:
            amount = self.discount_value
        return (self.customer_price - amount).quantize(Decimal('0.01'))

    @property
    def final_price(self):
        """Get the customer price after applying the admin margin and discount."""
        discounted_price = self.customer_discount_price
        return discounted_price if discounted_price is not None else self.customer_price


class ProductImage(models.Model):
    """
    Additional product images for multiple image support
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Product'
    )
    image = models.ImageField(
        upload_to='products/gallery/%Y/%m/',
        verbose_name='Image'
    )
    alt_text = models.CharField(max_length=200, blank=True, verbose_name='Alt Text')
    is_primary = models.BooleanField(default=False, verbose_name='Primary Image')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Product Image'
        verbose_name_plural = 'Product Images'
        ordering = ['-is_primary', 'created_at']

    def __str__(self):
        return f"Image for {self.product.name}"

    def save(self, *args, **kwargs):
        # If this is marked as primary, unmark other images for the same product
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).update(is_primary=False)
        super().save(*args, **kwargs)