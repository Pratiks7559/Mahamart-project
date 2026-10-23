from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from products.models import Category, Product
from PIL import Image, ImageDraw, ImageFont
import io
import os
from pathlib import Path

class Command(BaseCommand):
    help = 'Generate placeholder images for categories and products'

    def handle(self, *args, **options):
        self.stdout.write('Generating placeholder images...')
        
        # Create media directories if they don't exist
        media_dir = Path('media')
        (media_dir / 'products').mkdir(parents=True, exist_ok=True)
        (media_dir / 'categories').mkdir(parents=True, exist_ok=True)
        
        # Generate category placeholders
        categories = Category.objects.all()
        for category in categories:
            img = Image.new('RGB', (400, 400), color=(100, 149, 237))
            draw = ImageDraw.Draw(img)
            draw.text((200, 200), category.name[:2], fill='white', anchor='mm')
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG', quality=85)
            category.image.save(f'{category.slug}.jpg', ContentFile(img_io.getvalue()), save=True)
            self.stdout.write(f'Created image for category: {category.name}')
        
        # Generate product placeholders
        products = Product.objects.all()
        colors = [(220, 20, 60), (34, 139, 34), (255, 140, 0), (106, 90, 205)]
        for i, product in enumerate(products):
            color = colors[i % len(colors)]
            img = Image.new('RGB', (800, 600), color=color)
            draw = ImageDraw.Draw(img)
            # Add text
            draw.text((400, 300), product.name[:3], fill='white', anchor='mm')
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG', quality=85)
            product.main_image.save(f'{product.slug}.jpg', ContentFile(img_io.getvalue()), save=True)
            self.stdout.write(f'Created image for product: {product.name}')
        
        self.stdout.write(self.style.SUCCESS('All placeholder images created successfully!'))