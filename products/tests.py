from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from products.models import Category, Product


class PublicInfoPageTests(TestCase):
	def test_about_and_help_pages_render_with_working_navigation_links(self):
		about_response = self.client.get(reverse('products:about'))
		help_response = self.client.get(reverse('products:help_center'))

		self.assertEqual(about_response.status_code, 200)
		self.assertContains(about_response, 'Good finds.')
		self.assertContains(about_response, 'Explore the shop')
		self.assertContains(about_response, 'css/pages/info_pages.css')
		self.assertEqual(help_response.status_code, 200)
		self.assertContains(help_response, 'Frequently asked questions')
		self.assertContains(help_response, 'Apply to become a vendor')
		self.assertContains(help_response, 'css/pages/info_pages.css')

	def test_category_names_are_not_inserted_into_the_navbar(self):
		category = Category.objects.create(name='Seasonal Finds', slug='seasonal-finds')

		response = self.client.get(reverse('home'))
		navbar = response.content.decode().split('</nav>', 1)[0]

		self.assertNotIn(category.slug, navbar)
		self.assertIn(reverse('products:about'), navbar)
		self.assertIn(reverse('products:help_center'), navbar)
		self.assertIn(reverse('accounts:vendor_register'), navbar)


class VendorProductWorkflowTests(TestCase):
	def setUp(self):
		self.category = Category.objects.create(name='Food', slug='food')
		self.vendor = User.objects.create_user(
			username='vendor',
			email='vendor@example.com',
			password='Vendor-pass-2026!',
			is_vendor=True,
		)
		self.admin = User.objects.create_superuser(
			username='admin',
			email='admin@example.com',
			password='Admin-pass-2026!',
		)

	def test_vendor_submission_waits_for_admin_and_is_hidden_from_store(self):
		self.client.force_login(self.vendor)
		form_response = self.client.get(reverse('accounts:vendor_product_add'))
		self.assertEqual(form_response.status_code, 200)
		self.assertContains(form_response, 'Submit a product')
		self.assertContains(form_response, 'Percentage')

		response = self.client.post(reverse('accounts:vendor_product_add'), {
			'category': self.category.pk,
			'name': 'Vendor Tea',
			'description': 'Loose leaf tea',
			'price': '100.00',
			'stock': '8',
		})

		self.assertRedirects(response, reverse('accounts:vendor_portal'))
		product = Product.objects.get(name='Vendor Tea')
		self.assertEqual(product.vendor, self.vendor)
		self.assertEqual(product.review_status, Product.ReviewStatus.PENDING)
		self.assertFalse(product.is_active)
		self.assertNotContains(self.client.get(reverse('products:product_list')), 'Vendor Tea')

	def test_vendor_can_submit_percentage_discount(self):
		self.client.force_login(self.vendor)
		response = self.client.post(reverse('accounts:vendor_product_add'), {
			'category': self.category.pk,
			'name': 'Discounted Vendor Tea',
			'description': 'Loose leaf tea',
			'price': '100.00',
			'discount_type': Product.DiscountType.PERCENTAGE,
			'discount_value': '10.00',
			'stock': '8',
		})

		self.assertRedirects(response, reverse('accounts:vendor_portal'))
		product = Product.objects.get(name='Discounted Vendor Tea')
		self.assertEqual(product.discount_type, Product.DiscountType.PERCENTAGE)
		self.assertEqual(product.final_price, Decimal('90.00'))

	def test_vendor_portal_shows_scoped_product_and_stock_summary(self):
		Product.objects.create(
			category=self.category,
			vendor=self.vendor,
			name='Low Stock Tea',
			slug='low-stock-tea',
			price=Decimal('100.00'),
			stock=3,
			review_status=Product.ReviewStatus.APPROVED,
			is_active=True,
		)
		Product.objects.create(
			category=self.category,
			vendor=self.vendor,
			name='Sold Out Tea',
			slug='sold-out-tea',
			price=Decimal('120.00'),
			stock=0,
			review_status=Product.ReviewStatus.APPROVED,
			is_active=True,
		)
		Product.objects.create(
			category=self.category,
			vendor=self.vendor,
			name='Pending Tea',
			slug='pending-tea',
			price=Decimal('80.00'),
			stock=12,
			review_status=Product.ReviewStatus.PENDING,
			is_active=False,
		)
		Product.objects.create(
			category=self.category,
			name='Another Vendor Tea',
			slug='another-vendor-tea',
			price=Decimal('90.00'),
			stock=20,
		)
		self.client.force_login(self.vendor)

		response = self.client.get(reverse('accounts:vendor_portal'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Welcome back, vendor.')
		self.assertContains(response, 'Low Stock Tea')
		self.assertContains(response, 'Pending Tea')
		self.assertContains(response, 'Stock to check')
		self.assertNotContains(response, 'Another Vendor Tea')
		self.assertEqual(response.context['product_summary']['total'], 3)
		self.assertEqual(response.context['product_summary']['live'], 2)
		self.assertEqual(response.context['product_summary']['pending'], 1)
		self.assertEqual(response.context['product_summary']['low_stock'], 1)
		self.assertEqual(response.context['product_summary']['out_of_stock'], 1)
		self.assertEqual(response.context['product_summary']['live_stock_units'], 3)

	def test_admin_margin_is_added_when_product_is_approved(self):
		product = Product.objects.create(
			category=self.category,
			vendor=self.vendor,
			name='Vendor Tea',
			slug='vendor-tea',
			price=Decimal('100.00'),
			stock=8,
			review_status=Product.ReviewStatus.PENDING,
			is_active=False,
		)
		self.client.force_login(self.admin)
		queue_response = self.client.get(reverse('admin_dashboard:manage_vendor_products'))
		self.assertEqual(queue_response.status_code, 200)
		self.assertContains(queue_response, 'Vendor Tea')
		self.assertContains(queue_response, 'Add margin')

		response = self.client.post(
			reverse('admin_dashboard:review_vendor_product', args=[product.pk]),
			{'margin': '25.50', 'action': 'approve'},
		)

		self.assertRedirects(response, reverse('admin_dashboard:manage_vendor_products'))
		product.refresh_from_db()
		self.assertEqual(product.review_status, Product.ReviewStatus.APPROVED)
		self.assertTrue(product.is_active)
		self.assertEqual(product.final_price, Decimal('125.50'))
		self.assertContains(self.client.get(reverse('products:product_list')), '₹125.50')

	def test_flat_and_percentage_discounts_are_subtracted_from_customer_price(self):
		flat_product = Product.objects.create(
			category=self.category,
			name='Flat discount item',
			slug='flat-discount-item',
			price=Decimal('100.00'),
			admin_margin=Decimal('20.00'),
			discount_type=Product.DiscountType.FLAT,
			discount_value=Decimal('15.00'),
		)
		percentage_product = Product.objects.create(
			category=self.category,
			name='Percentage discount item',
			slug='percentage-discount-item',
			price=Decimal('100.00'),
			admin_margin=Decimal('20.00'),
			discount_type=Product.DiscountType.PERCENTAGE,
			discount_value=Decimal('10.00'),
		)

		self.assertEqual(flat_product.final_price, Decimal('105.00'))
		self.assertEqual(percentage_product.final_price, Decimal('108.00'))
		self.assertEqual(percentage_product.discount_percentage, 10)
