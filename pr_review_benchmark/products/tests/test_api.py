from decimal import Decimal

import pytest
from django.urls import reverse
from rest_framework import status

from pr_review_benchmark.products.factories import (
    CategoryFactory,
    InventoryFactory,
    ProductFactory,
    SupplierFactory,
)
from pr_review_benchmark.products.models import PriceHistory, Product


@pytest.mark.django_db
class TestProductViewSet:
    def test_list_products(self, authenticated_client):
        ProductFactory.create_batch(3)
        response = authenticated_client.get(reverse("product-list"))
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

    def test_list_unauthenticated(self, api_client):
        response = api_client.get(reverse("product-list"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_product(self, authenticated_client):
        category = CategoryFactory()
        supplier = SupplierFactory()
        data = {
            "name": "New Product",
            "sku": "NEW-001",
            "price": "49.99",
            "category": category.pk,
            "supplier": supplier.pk,
        }
        response = authenticated_client.post(reverse("product-list"), data, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.filter(sku="NEW-001").exists()

    def test_retrieve_product(self, authenticated_client):
        product = ProductFactory()
        response = authenticated_client.get(reverse("product-detail", args=[product.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["sku"] == product.sku

    def test_update_product(self, authenticated_client):
        product = ProductFactory()
        data = {
            "name": "Updated Name",
            "sku": product.sku,
            "price": str(product.price),
            "category": product.category.pk,
            "supplier": product.supplier.pk,
        }
        response = authenticated_client.put(reverse("product-detail", args=[product.pk]), data, format="json")
        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert product.name == "Updated Name"

    def test_delete_product(self, authenticated_client):
        product = ProductFactory()
        response = authenticated_client.delete(reverse("product-detail", args=[product.pk]))
        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
class TestCategoryViewSet:
    def test_list_categories(self, authenticated_client):
        CategoryFactory.create_batch(3)
        response = authenticated_client.get(reverse("category-list"))
        assert response.status_code == status.HTTP_200_OK

    def test_create_category(self, authenticated_client):
        data = {"name": "New Category", "slug": "new-category"}
        response = authenticated_client.post(reverse("category-list"), data, format="json")
        assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
class TestStockAPIView:
    def test_get_stock(self, authenticated_client):
        product = ProductFactory()
        InventoryFactory(product=product, quantity=50)
        response = authenticated_client.get(reverse("product-stock", args=[product.pk]))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == 50


@pytest.mark.django_db
class TestUpdatePriceAPIView:
    def test_update_price(self, authenticated_client):
        product = ProductFactory(price=Decimal("10.00"))
        data = {"new_price": "15.00"}
        response = authenticated_client.post(
            reverse("product-update-price", args=[product.pk]), data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["new_price"] == "15.00"
        assert PriceHistory.objects.filter(product=product).exists()

    def test_update_price_negative(self, authenticated_client):
        product = ProductFactory()
        data = {"new_price": "-5.00"}
        response = authenticated_client.post(
            reverse("product-update-price", args=[product.pk]), data, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestRestockAPIView:
    def test_restock(self, authenticated_client):
        product = ProductFactory()
        InventoryFactory(product=product, quantity=10)
        data = {"quantity": 20}
        response = authenticated_client.post(
            reverse("product-restock", args=[product.pk]), data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["quantity"] == 30
