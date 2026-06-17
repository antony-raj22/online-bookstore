import json
from decimal import Decimal

from django.test import TestCase, override_settings

from .models import Book


@override_settings(ALLOWED_HOSTS=['testserver'])
class PublicRouteSmokeTests(TestCase):
    def setUp(self):
        self.book = Book.objects.create(
            title='Smoke Test Book',
            author='Test Author',
            description='A book used by route smoke tests.',
            price=Decimal('199.00'),
            cover_url='https://example.com/book.jpg',
            stock=3,
            genre='fiction',
        )

    def test_public_template_routes_render(self):
        paths = [
            '/',
            f'/book/{self.book.id}/',
            '/categories/',
            '/subscribe/',
            '/track-order/',
            '/register/',
            '/login/',
            '/password-reset/',
            '/password-reset/done/',
            '/reset/done/',
        ]

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)

    def test_public_api_routes_return_json(self):
        paths = [
            '/api/bootstrap/',
            '/api/books/',
            f'/api/books/{self.book.id}/',
            '/api/categories/',
            '/api/cart/',
        ]

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers['Content-Type'], 'application/json')

    def test_cart_update_removes_items_when_stock_is_unavailable(self):
        self.book.stock = 0
        self.book.save(update_fields=['stock'])
        session = self.client.session
        session['cart'] = {str(self.book.id): 1}
        session.save()

        response = self.client.post(
            '/api/cart/update/',
            data=json.dumps({str(self.book.id): 1}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['items'], [])
        self.assertEqual(self.client.session['cart'], {})
