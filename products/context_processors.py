from products.models import Category

def categories(request):
    """
    Context processor to add categories to all templates
    """
    return {
        'categories': Category.objects.filter(is_active=True).order_by('name')
    }