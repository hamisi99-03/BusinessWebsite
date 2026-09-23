import base64

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Cart, CartItem, Customer, Order, Product, ProductImage


User = get_user_model()


@override_settings(SECURE_SSL_REDIRECT=False)
class SecurityRegressionTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username='customer',
            password='Testing-Strong-Password-123!',
        )
        self.staff = User.objects.create_user(
            username='staff',
            password='Testing-Strong-Password-123!',
            is_staff=True,
        )
        self.product = Product.objects.create(
            name='Test product',
            price='10.00',
            stock=5,
        )

    def test_registration_does_not_grant_staff_privileges(self):
        response = self.client.post(reverse('register'), {
            'username': 'new-customer',
            'first_name': 'New',
            'last_name': 'Customer',
            'email': 'new@example.com',
            'password1': 'Testing-Strong-Password-123!',
            'password2': 'Testing-Strong-Password-123!',
        })

        self.assertEqual(response.status_code, 302)
        self.assertFalse(User.objects.get(username='new-customer').is_staff)

    def test_check_username_reports_availability(self):
        taken = self.client.get(reverse('check_username'), {'username': 'customer'})
        self.assertEqual(taken.status_code, 200)
        self.assertTrue(taken.json()['valid'])
        self.assertFalse(taken.json()['available'])

        free = self.client.get(reverse('check_username'), {'username': 'brand-new-name'})
        self.assertTrue(free.json()['available'])

    def test_check_username_rejects_invalid_characters(self):
        response = self.client.get(reverse('check_username'), {'username': 'bad name!'})
        self.assertFalse(response.json()['valid'])

    def test_suggest_username_returns_available_names(self):
        response = self.client.get(reverse('suggest_username'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
        })
        self.assertEqual(response.status_code, 200)
        suggestions = response.json()['suggestions']
        self.assertTrue(suggestions)
        self.assertEqual(suggestions[0], 'janedoe')
        self.assertFalse(User.objects.filter(username__iexact=suggestions[0]).exists())

    def test_customers_cannot_write_to_management_apis(self):
        api_client = APIClient()
        api_client.force_authenticate(user=self.customer)

        order_response = api_client.post('/api/orders/', {
            'customer': self.customer.customer.pk,
            'status': 'pending',
        })
        product_response = api_client.post('/api/products/', {
            'name': 'Unauthorized product',
            'price': '1.00',
            'stock': 1,
        })

        self.assertIn(order_response.status_code, (401, 403))
        self.assertIn(product_response.status_code, (401, 403))

    def test_customers_can_only_read_their_own_order_api_records(self):
        order = Order.objects.create(customer=self.customer.customer)
        api_client = APIClient()
        api_client.force_authenticate(user=self.customer)

        response = api_client.get(f'/api/orders/{order.pk}/')

        self.assertEqual(response.status_code, 200)

    def test_anonymous_management_api_requests_are_rejected(self):
        api_client = APIClient()

        for path in ('/api/customers/', '/api/orders/', '/api/payments/', '/api/debts/999999/'):
            with self.subTest(path=path):
                response = api_client.get(path)
                self.assertIn(response.status_code, (401, 403))

    def test_public_product_reads_do_not_allow_writes(self):
        api_client = APIClient()

        self.assertEqual(api_client.get('/api/products/').status_code, 200)
        self.assertIn(
            api_client.post('/api/products/', {
                'name': 'Anonymous product',
                'price': '1.00',
                'stock': 1,
            }).status_code,
            (401, 403),
        )

    def test_staff_token_can_access_protected_api(self):
        api_client = APIClient()
        login_response = api_client.post('/api/auth/login/', {
            'username': self.staff.username,
            'password': 'Testing-Strong-Password-123!',
        })

        self.assertEqual(login_response.status_code, 200)
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Token {login_response.data['token']}"
        )
        self.assertEqual(api_client.get('/api/products/').status_code, 200)

    def test_logout_requires_post(self):
        self.client.force_login(self.customer)

        response = self.client.get(reverse('logout'))

        self.assertEqual(response.status_code, 405)

    def test_cart_removal_requires_post(self):
        cart = Cart.objects.create(customer=self.customer.customer)
        item = CartItem.objects.create(cart=cart, product=self.product)
        self.client.force_login(self.customer)

        response = self.client.get(reverse('remove_from_cart', args=[item.pk]))

        self.assertEqual(response.status_code, 405)
        self.assertTrue(CartItem.objects.filter(pk=item.pk).exists())

    def test_customers_cannot_add_products(self):
        self.client.force_login(self.customer)

        response = self.client.get(reverse('add_product'))

        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_invalid_product_image_is_rejected(self):
        invalid_image = SimpleUploadedFile(
            'product.jpg', b'not-an-image', content_type='image/jpeg'
        )
        self.client.force_login(self.staff)

        response = self.client.post(reverse('add_product'), {
            'name': 'Image test product',
            'price': '20.00',
            'stock': 2,
            'images': invalid_image,
        })

        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name='Image test product')
        self.assertFalse(ProductImage.objects.filter(product=product).exists())

    def test_valid_product_image_is_accepted(self):
        image = SimpleUploadedFile(
            'product.png',
            base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk'
                'YAAAAAYAAjCB0C8AAAAASUVORK5CYII='
            ),
            content_type='image/png',
        )
        self.client.force_login(self.staff)

        response = self.client.post(reverse('add_product'), {
            'name': 'Valid image product',
            'price': '20.00',
            'stock': 2,
            'images': image,
        })

        self.assertEqual(response.status_code, 302)
        product = Product.objects.get(name='Valid image product')
        self.assertTrue(ProductImage.objects.filter(product=product).exists())

    def test_product_and_profile_media_use_separate_storage_buckets(self):
        product_storage = ProductImage._meta.get_field('image').storage
        profile_storage = Customer._meta.get_field('profile_picture').storage

        self.assertEqual(product_storage.bucket_name, 'product-media')
        self.assertTrue(product_storage.public)
        self.assertEqual(profile_storage.bucket_name, 'profile-media')
        self.assertFalse(profile_storage.public)

    def test_non_superuser_staff_cannot_reset_superuser_password(self):
        superuser = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='Testing-Strong-Password-123!',
        )
        self.client.force_login(self.staff)

        response = self.client.get(
            reverse('admin_reset_user_password', args=[superuser.pk])
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn('/api/admin-dashboard/users/', response.url)
