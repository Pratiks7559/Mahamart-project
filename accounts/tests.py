from io import BytesIO
import tempfile
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from .models import User, VendorApplication
from products.models import Category
from .forms import VendorApplicationForm


def shop_image():
	content = BytesIO()
	Image.new('RGB', (1, 1), color='white').save(content, format='PNG')
	return SimpleUploadedFile('shop.png', content.getvalue(), content_type='image/png')


class LoginPageTests(TestCase):
	def test_login_page_displays_brand_panel_and_login_options(self):
		response = self.client.get('/accounts/login/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Good to see you again.')
		self.assertContains(response, 'Something lovely is waiting.')
		self.assertContains(response, 'User Login')
		self.assertContains(response, 'Vendor Login')

	def test_vendor_login_page_displays_brand_panel_and_login_fields(self):
		response = self.client.get('/accounts/vendor/login/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'YOUR VENDOR SPACE')
		self.assertContains(response, 'Your next big idea starts here.')
		self.assertContains(response, 'vendor_id_12345')
		self.assertContains(response, 'name="username"')
		self.assertContains(response, 'name="password"')

	def test_vendor_login_reports_pending_approval_only_for_pending_application(self):
		user = User.objects.create_user(
			username='pending-vendor',
			email='pending@example.com',
			password='Pending-vendor-2026!',
		)
		VendorApplication.objects.create(
			applicant=user,
			full_name='Pending Vendor',
			email=user.email,
			address='Main street',
			shop_name='Pending Shop',
			registration_number='REG-12345',
			gst_number='22AAAAA0000A1Z5',
			products_by_category={'Food': ['tea']},
			phone='9876543210',
			pan_number='ABCDE1234F',
			aadhaar_number='123456789012',
		)

		response = self.client.post('/accounts/vendor/login/', {
			'username': user.username,
			'password': 'Pending-vendor-2026!',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'still awaiting admin approval')

	def test_inactive_vendor_login_reports_account_status(self):
		User.objects.create_user(
			username='inactive-vendor',
			email='inactive@example.com',
			password='Inactive-vendor-2026!',
			is_vendor=True,
			is_active=False,
		)

		response = self.client.post('/accounts/vendor/login/', {
			'username': 'inactive-vendor',
			'password': 'Inactive-vendor-2026!',
		})

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'vendor account is inactive')


class VendorApplicationFormTests(TestCase):
	def test_vendor_registration_page_renders(self):
		response = self.client.get('/accounts/vendor/register/')

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Vendor Registration')

	def test_logged_in_customer_can_submit_vendor_application(self):
		category = Category.objects.create(name='Grocery', slug='grocery')
		user = User.objects.create_user(
			username='shopper',
			email='mira@example.com',
			password='Shopper-pass-2026!',
			phone='+919876543210',
			full_name='Mira Shah',
		)
		self.client.force_login(user)
		data = {
			'full_name': 'Mira Shah',
			'email': 'mira@example.com',
			'address': 'Main street',
			'shop_name': 'Mira Foods',
			'registration_number': 'REG-12345',
			'gst_number': '22aaaaa0000a1z5',
			'categories': [category.pk],
			'products_by_category': 'Grocery: flour, rice',
			'phone': '+91 98765-43210',
			'pan_number': 'abcde1234f',
			'aadhaar_number': '1234 5678 9012',
			'shop_photo': shop_image(),
		}

		with tempfile.TemporaryDirectory() as media_root, override_settings(MEDIA_ROOT=media_root):
			response = self.client.post('/accounts/vendor/register/', data, follow=True)

			self.assertEqual(response.status_code, 200)
			self.assertContains(response, 'Form submitted successfully')
			application = VendorApplication.objects.get(email='mira@example.com')
			self.assertEqual(application.applicant, user)
			self.assertEqual(application.gst_number, '22AAAAA0000A1Z5')
			self.assertEqual(application.pan_number, 'ABCDE1234F')
			self.assertEqual(application.phone, '+919876543210')
			self.assertEqual(application.aadhaar_number, '123456789012')
			application.shop_photo.delete(save=False)

	def test_valid_application_requires_products_for_selected_category(self):
		category = Category.objects.create(name='Food', slug='food')
		image = shop_image()
		form = VendorApplicationForm(data={
			'full_name': 'Mira Shah',
			'email': 'mira@example.com',
			'address': 'Main street',
			'shop_name': 'Mira Foods',
			'registration_number': 'REG-12345',
			'gst_number': '22AAAAA0000A1Z5',
			'categories': [category.pk],
			'products_by_category': 'Food: tea, coffee',
			'phone': '9876543210',
			'pan_number': 'ABCDE1234F',
			'aadhaar_number': '123456789012',
		}, files={'shop_photo': image})

		self.assertTrue(form.is_valid(), form.errors)
		self.assertEqual(form.cleaned_data['products_by_category'], {'Food': ['tea', 'coffee']})
		self.assertEqual(form.cleaned_data['gst_number'], '22AAAAA0000A1Z5')
		self.assertEqual(form.cleaned_data['pan_number'], 'ABCDE1234F')
		self.assertEqual(form.cleaned_data['phone'], '9876543210')
		self.assertEqual(form.cleaned_data['aadhaar_number'], '123456789012')

	def test_single_category_accepts_plain_product_list(self):
		category = Category.objects.create(name='Food', slug='food')
		form = VendorApplicationForm(data={
			'full_name': 'Mira Shah',
			'email': 'mira@example.com',
			'address': 'Main street',
			'shop_name': 'Mira Foods',
			'registration_number': 'REG-12345',
			'gst_number': '22AAAAA0000A1Z5',
			'categories': [category.pk],
			'products_by_category': 'tea, coffee',
			'phone': '9876543210',
			'pan_number': 'ABCDE1234F',
			'aadhaar_number': '123456789012',
		}, files={'shop_photo': shop_image()})

		self.assertTrue(form.is_valid(), form.errors)
		self.assertEqual(form.cleaned_data['products_by_category'], {'Food': ['tea', 'coffee']})

	def test_application_rejects_products_for_unselected_category(self):
		category = Category.objects.create(name='Food', slug='food')
		image = shop_image()
		form = VendorApplicationForm(data={
			'full_name': 'Mira Shah',
			'email': 'mira@example.com',
			'address': 'Main street',
			'shop_name': 'Mira Foods',
			'registration_number': 'REG-12345',
			'gst_number': '22AAAAA0000A1Z5',
			'categories': [category.pk],
			'products_by_category': 'Clothing: shirts',
			'phone': '9876543210',
			'pan_number': 'ABCDE1234F',
			'aadhaar_number': '123456789012',
		}, files={'shop_photo': image})

		self.assertFalse(form.is_valid())
		self.assertIn('products_by_category', form.errors)
