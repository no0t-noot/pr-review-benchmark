import pytest
from django.test import Client
from django.urls import reverse

from pr_review_benchmark.products.factories import (
    CategoryFactory,
    InventoryFactory,
    ProductFactory,
)


@pytest.mark.django_db
class TestProductListView:
    def test_list_view(self, client: Client):
        ProductFactory.create_batch(3)
        response = client.get(reverse("products:product-list"))
        assert response.status_code == 200
        assert len(response.context["products"]) == 3

    def test_only_active_products(self, client: Client):
        ProductFactory(is_active=True)
        ProductFactory(is_active=False)
        response = client.get(reverse("products:product-list"))
        assert len(response.context["products"]) == 1


@pytest.mark.django_db
class TestProductDetailView:
    def test_detail_view(self, client: Client):
        product = ProductFactory()
        response = client.get(reverse("products:product-detail", args=[product.pk]))
        assert response.status_code == 200
        assert response.context["product"] == product


@pytest.mark.django_db
class TestDashboardView:
    def test_dashboard(self, client: Client):
        category = CategoryFactory()
        product = ProductFactory(category=category)
        InventoryFactory(product=product, quantity=5, low_stock_threshold=10)
        response = client.get(reverse("dashboard"))
        assert response.status_code == 200
        assert response.context["total_products"] == 1
