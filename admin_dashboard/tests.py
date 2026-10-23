from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from accounts.models import User, VendorApplication


class AdminNavigationLogoutTests(TestCase):
	def setUp(self):
		self.admin = User.objects.create_superuser(
			username='admin',
			email='admin@example.com',
			password='Admin-pass-2026!',
		)
		self.client.force_login(self.admin)

	def test_admin_dashboard_has_direct_store_and_logout_actions_without_dropdown(self):
		response = self.client.get(reverse('admin_dashboard:dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'View Store')
		self.assertContains(response, 'Logout')
		self.assertNotContains(response, 'admin-profile-btn')
		self.assertNotContains(response, 'admin-dropdown-menu')

	def test_storefront_shows_vendor_applications_and_admin_logout_without_user_dropdown(self):
		response = self.client.get(reverse('home'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'class="navbar navbar-admin"')
		self.assertContains(response, 'Vendor Applications')
		self.assertContains(response, 'action="/admin-dashboard/logout/"')
		self.assertNotContains(response, 'class="user-dropdown"')

	def test_admin_logout_requires_post_and_clears_admin_session(self):
		logout_url = reverse('admin_dashboard:admin_logout')
		get_response = self.client.get(logout_url)

		self.assertEqual(get_response.status_code, 405)
		self.assertEqual(self.client.get(reverse('admin_dashboard:dashboard')).status_code, 200)

		response = self.client.post(logout_url)

		self.assertRedirects(response, reverse('admin_dashboard:admin_login'))
		self.assertEqual(self.client.get(reverse('admin_dashboard:dashboard')).status_code, 302)


class AdminLoginShortcutTests(TestCase):
	def test_admin_login_shortcut_renders_admin_login_page(self):
		for url in ('/admin-login', '/admin-login/'):
			with self.subTest(url=url):
				response = self.client.get(url)

				self.assertEqual(response.status_code, 200)
				self.assertTemplateUsed(response, 'admin_dashboard/admin_login.html')
				self.assertContains(response, 'Admin Login')


class VendorApprovalTests(TestCase):
	@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
	def test_approval_promotes_linked_customer_account(self):
		admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='Admin-pass-2026!')
		customer = User.objects.create_user(
			username='shopper',
			email='mira@example.com',
			password='Shopper-pass-2026!',
			phone='9876543210',
			full_name='Mira Shah',
			is_active=False,
		)
		application = VendorApplication.objects.create(
			applicant=customer,
			full_name='Mira Shah',
			email='mira@example.com',
			address='Main street',
			shop_name='Mira Foods',
			registration_number='REG-12345',
			gst_number='22AAAAA0000A1Z5',
			products_by_category={'Grocery': ['rice']},
			phone='9876543210',
			pan_number='ABCDE1234F',
			aadhaar_number='123456789012',
		)
		self.client.force_login(admin)

		response = self.client.post(f'/admin-dashboard/vendors/{application.pk}/approve/', {
			'username': 'mira-vendor',
			'password': 'Vendor-Secure-2026!',
		})

		self.assertRedirects(response, '/admin-dashboard/vendors/')
		customer.refresh_from_db()
		self.assertTrue(customer.is_vendor)
		self.assertTrue(customer.is_active)
		self.assertEqual(customer.username, 'mira-vendor')
		self.assertTrue(customer.check_password('Vendor-Secure-2026!'))
		self.assertEqual(User.objects.filter(email='mira@example.com').count(), 1)

	@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
	def test_approval_creates_vendor_and_emails_credentials(self):
		admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='Admin-pass-2026!')
		application = VendorApplication.objects.create(
			full_name='Mira Shah',
			email='mira@example.com',
			address='Main street',
			shop_name='Mira Foods',
			registration_number='REG-12345',
			gst_number='22AAAAA0000A1Z5',
			products_by_category={'Food': ['tea']},
			phone='9876543210',
			pan_number='ABCDE1234F',
			aadhaar_number='123456789012',
		)
		self.client.force_login(admin)
		queue_response = self.client.get('/admin-dashboard/vendors/pending/')
		self.assertEqual(queue_response.status_code, 200)
		self.assertContains(queue_response, 'Mira Foods')

		response = self.client.post(f'/admin-dashboard/vendors/{application.pk}/approve/', {
			'username': 'mira-vendor',
			'password': 'Vendor-Secure-2026!',
		})

		self.assertRedirects(response, '/admin-dashboard/vendors/')
		vendor = User.objects.get(username='mira-vendor')
		self.assertTrue(vendor.is_vendor)
		self.assertTrue(vendor.check_password('Vendor-Secure-2026!'))
		self.assertNotEqual(vendor.password, 'Vendor-Secure-2026!')
		application.refresh_from_db()
		self.assertEqual(application.status, VendorApplication.Status.APPROVED)
		self.assertEqual(len(mail.outbox), 1)
		self.assertIn('mira@example.com', mail.outbox[0].to)
		self.assertIn('Vendor-Secure-2026!', mail.outbox[0].body)

		self.client.logout()
		login_response = self.client.post('/accounts/vendor/login/', {
			'username': 'mira-vendor',
			'password': 'Vendor-Secure-2026!',
		})
		self.assertRedirects(login_response, '/accounts/vendor/')
		portal_response = self.client.get('/accounts/vendor/')
		self.assertEqual(portal_response.status_code, 200)
		self.assertContains(portal_response, 'mira-vendor')


class VendorApplicationDetailTests(TestCase):
	def test_vendor_list_hides_private_details_until_view_details_is_opened(self):
		admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='Admin-pass-2026!')
		application = VendorApplication.objects.create(
			full_name='Mira Shah',
			email='mira@example.com',
			address='Private business address',
			shop_name='Mira Foods',
			registration_number='REG-12345',
			gst_number='22AAAAA0000A1Z5',
			products_by_category={'Food': ['tea']},
			phone='9876543210',
			pan_number='ABCDE1234F',
			aadhaar_number='123456789012',
			status=VendorApplication.Status.APPROVED,
		)
		pending_application = VendorApplication.objects.create(
			full_name='Pending Owner',
			email='pending@example.com',
			address='Pending business address',
			shop_name='Pending Shop',
			registration_number='REG-54321',
			gst_number='22BBBBB0000B1Z5',
			products_by_category={'Food': ['coffee']},
			phone='9876543211',
			pan_number='BCDEF1234G',
			aadhaar_number='123456789013',
			status=VendorApplication.Status.PENDING,
		)
		self.client.force_login(admin)

		overview_response = self.client.get('/admin-dashboard/vendors/')
		self.assertContains(overview_response, 'Pending applications')
		self.assertContains(overview_response, 'Approved applications')
		self.assertContains(overview_response, 'Rejected applications')
		self.assertContains(overview_response, 'href="/admin-dashboard/vendors/pending/"')
		self.assertContains(overview_response, 'href="/admin-dashboard/vendors/approved/"')

		pending_response = self.client.get('/admin-dashboard/vendors/pending/')
		self.assertContains(pending_response, 'Pending Shop')
		self.assertNotContains(pending_response, 'Mira Foods')
		self.assertEqual(pending_response.context['applications'].get(), pending_application)

		approved_response = self.client.get('/admin-dashboard/vendors/approved/')
		self.assertContains(approved_response, 'Mira Foods')
		self.assertNotContains(approved_response, 'Pending Shop')
		self.assertEqual(approved_response.context['applications'].get(), application)
		self.assertContains(approved_response, 'View details')
		self.assertNotContains(approved_response, 'mira@example.com')
		self.assertNotContains(approved_response, 'ABCDE1234F')
		self.assertNotContains(approved_response, '123456789012')

		detail_response = self.client.get(f'/admin-dashboard/vendors/{application.pk}/')
		self.assertContains(detail_response, 'mira@example.com')
		self.assertContains(detail_response, 'ABCDE1234F')
		self.assertContains(detail_response, '123456789012')
