from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed the database with sample categories and products'

    def handle(self, *args, **options):
        self.stdout.write('🌱 Seeding database with sample data...')
        
        # Create Categories
        categories_data = [
            {'name': 'Electronics', 'description': 'Latest gadgets and electronic devices'},
            {'name': 'Clothing', 'description': 'Fashionable apparel for men and women'},
            {'name': 'Books', 'description': 'Best selling books and e-books'},
        ]
        
        categories = {}
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={
                    'slug': slugify(cat_data['name']),
                    'description': cat_data['description'],
                    'is_active': True
                }
            )
            categories[cat_data['name']] = category
            if created:
                self.stdout.write(f'  ✅ Created category: {category.name}')
            else:
                self.stdout.write(f'  ⏭️ Category already exists: {category.name}')
        
        # Create Products
        products_data = [
            {
                'category': 'Electronics',
                'name': 'Premium Wireless Headphones Pro',
                'sku': 'PROD-1001',
                'description': 'Experience crystal-clear audio with our premium wireless headphones. Features active noise cancellation, 40-hour battery life, and ultra-comfortable ear cushions.',
                'price': Decimal('299.99'),
                'discount_value': Decimal('100.00'),
                'stock': 45,
                'is_featured': True
            },
            {
                'category': 'Electronics',
                'name': '4K Smart TV 55 Inch',
                'sku': 'PROD-1002',
                'description': 'Immerse yourself in stunning 4K HDR quality with this 55-inch Smart TV. Features built-in streaming apps, voice control, and Dolby Atmos sound.',
                'price': Decimal('699.99'),
                'discount_value': None,
                'stock': 15,
                'is_featured': True
            },
            {
                'category': 'Clothing',
                'name': 'Premium Leather Jacket',
                'sku': 'PROD-1003',
                'description': 'Handcrafted premium leather jacket with a modern fit. Features a soft inner lining, multiple pockets, and durable zippers.',
                'price': Decimal('249.99'),
                'discount_value': Decimal('60.00'),
                'stock': 30,
                'is_featured': True
            },
            {
                'category': 'Clothing',
                'name': 'Classic Denim Jeans',
                'sku': 'PROD-1004',
                'description': 'Timeless classic denim jeans with a perfect fit. Made from high-quality cotton blend fabric, available in all sizes.',
                'price': Decimal('79.99'),
                'discount_value': None,
                'stock': 100,
                'is_featured': False
            },
            {
                'category': 'Books',
                'name': 'The Complete Python Programming Guide',
                'sku': 'PROD-1005',
                'description': 'Master Python programming with this comprehensive guide. Covers everything from basics to advanced topics.',
                'price': Decimal('49.99'),
                'discount_value': Decimal('20.00'),
                'stock': 75,
                'is_featured': True
            },
            {
                'category': 'Books',
                'name': 'The Art of Minimalism',
                'sku': 'PROD-1006',
                'description': 'Discover the transformative power of minimalism in this inspiring book. Learn how to declutter your life.',
                'price': Decimal('34.99'),
                'discount_value': None,
                'stock': 50,
                'is_featured': False
            },
            {
                'category': 'Electronics',
                'name': 'Smart Fitness Band X2',
                'sku': 'PROD-1007',
                'description': 'Track your fitness goals with our advanced smart band. Features heart rate monitor, sleep tracking, and GPS.',
                'price': Decimal('149.99'),
                'discount_value': Decimal('30.00'),
                'stock': 60,
                'is_featured': True
            },
            {
                'category': 'Clothing',
                'name': 'Sporty Sneakers',
                'sku': 'PROD-1008',
                'description': 'Comfortable and stylish sporty sneakers perfect for everyday wear. Features cushioned insoles and breathable fabric.',
                'price': Decimal('89.99'),
                'discount_value': Decimal('20.00'),
                'stock': 40,
                'is_featured': True
            },
            {
                'category': 'Electronics',
                'name': 'Ultra-Slim Laptop',
                'sku': 'PROD-1009',
                'description': 'Powerful ultra-slim laptop with 16GB RAM, 512GB SSD, and 14-inch 4K display.',
                'price': Decimal('1199.99'),
                'discount_value': Decimal('200.00'),
                'stock': 10,
                'is_featured': True
            },
            {
                'category': 'Books',
                'name': 'Business Strategy & Leadership',
                'sku': 'PROD-1010',
                'description': 'Learn effective business strategies and leadership skills from industry experts.',
                'price': Decimal('39.99'),
                'discount_value': None,
                'stock': 65,
                'is_featured': False
            },
            {
                'category': 'Clothing',
                'name': 'Designer Watch',
                'sku': 'PROD-1011',
                'description': 'Elegant designer watch with a premium leather strap and stainless steel case.',
                'price': Decimal('199.99'),
                'discount_value': Decimal('50.00'),
                'stock': 25,
                'is_featured': True
            },
            {
                'category': 'Electronics',
                'name': 'Professional Drone 4K',
                'sku': 'PROD-1012',
                'description': 'Professional-grade drone with 4K camera, 30-minute flight time, and obstacle avoidance.',
                'price': Decimal('799.99'),
                'discount_value': Decimal('150.00'),
                'stock': 8,
                'is_featured': True
            }
        ]
        
        for prod_data in products_data:
            category = categories.get(prod_data['category'])
            if not category:
                self.stdout.write(f'  ❌ Category not found: {prod_data["category"]}')
                continue
            
            product, created = Product.objects.get_or_create(
                sku=prod_data['sku'],
                defaults={
                    'category': category,
                    'name': prod_data['name'],
                    'slug': slugify(prod_data['name']),
                    'description': prod_data['description'],
                    'price': prod_data['price'],
                    'discount_type': Product.DiscountType.FLAT,
                    'discount_value': prod_data['discount_value'],
                    'stock': prod_data['stock'],
                    'is_featured': prod_data.get('is_featured', False),
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(f'  ✅ Created product: {product.name}')
            else:
                self.stdout.write(f'  ⏭️ Product already exists: {product.name}')
        
        self.stdout.write(self.style.SUCCESS('✅ Database seeded successfully!'))