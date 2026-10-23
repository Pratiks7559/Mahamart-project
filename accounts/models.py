from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class User(AbstractUser):
    # Add phone field with validation
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        blank=True,  # Allow blank for existing users
        null=True,   # Allow null for existing users
        default=None # Default to None
    )
    full_name = models.CharField(max_length=100, blank=True, default='')
    address = models.TextField(blank=True, default='')
    profile_picture = models.ImageField(
        upload_to='profiles/%Y/%m/',
        blank=True,
        null=True
    )
    is_phone_verified = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.username or self.email or str(self.id)
    
    def get_profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return '/static/images/default-avatar.png'


class VendorApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    applicant = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vendor_applications',
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    address = models.TextField()
    shop_name = models.CharField(max_length=150)
    registration_number = models.CharField(max_length=100)
    gst_number = models.CharField(max_length=15)
    categories = models.ManyToManyField('products.Category', related_name='vendor_applications')
    products_by_category = models.JSONField(default=dict)
    shop_photo = models.ImageField(upload_to='vendors/shops/%Y/%m/')
    phone = models.CharField(max_length=15)
    pan_number = models.CharField(max_length=10)
    aadhaar_number = models.CharField(max_length=12)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.shop_name} ({self.get_status_display()})'

    def mark_reviewed(self, status):
        self.status = status
        self.reviewed_at = timezone.now()
        self.save(update_fields=['status', 'reviewed_at'])