from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from .models import Brand, Category


class ProductAPITestCase(APITestCase):
    def setUp(self):
        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin_user)

        # Create brand & category
        self.brand = Brand.objects.create(name="TestBrand", slug="testbrand")
        self.category = Category.objects.create(
            name="TestCategory", slug="testcategory"
        )

    def test_create_product(self):
        url = reverse("product-list")
        data = {
            "name": "Test Product",
            "slug": "test-product",
            "brand_id": self.brand.id,
            "category_id": self.category.id,
            "description": "A sample product",
            "price": 9.99,
            "rating": 4.5,
            "in_stock": True,
            "image_url": "http://example.com/image.png",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
