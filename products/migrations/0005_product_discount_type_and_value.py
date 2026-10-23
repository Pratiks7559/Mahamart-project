from decimal import Decimal

from django.db import migrations, models
import django.core.validators


def migrate_discount_prices(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.exclude(discount_price__isnull=True).iterator():
        if product.price is not None:
            product.discount_value = product.price - product.discount_price
            product.save(update_fields=['discount_value'])


def restore_discount_prices(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.exclude(discount_value__isnull=True).iterator():
        if product.price is not None:
            product.discount_price = product.price - product.discount_value
            product.save(update_fields=['discount_price'])


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0004_product_admin_margin_product_review_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='discount_type',
            field=models.CharField(choices=[('flat', 'Flat amount'), ('percentage', 'Percentage')], default='flat', max_length=10),
        ),
        migrations.AddField(
            model_name='product',
            name='discount_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.RunPython(migrate_discount_prices, restore_discount_prices),
        migrations.RemoveField(
            model_name='product',
            name='discount_price',
        ),
        migrations.AlterField(
            model_name='product',
            name='discount_value',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(Decimal('0.01'))], verbose_name='Discount Value'),
        ),
    ]