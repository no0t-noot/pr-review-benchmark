
import pytest

from pr_review_benchmark.products.factories import CategoryFactory, ProductFactory, SupplierFactory
from pr_review_benchmark.products.serializers import (
    CategorySerializer,
    PriceUpdateSerializer,
    ProductCreateUpdateSerializer,
    RestockSerializer,
)


@pytest.mark.django_db
class TestCategorySerializer:
    def test_serialize(self):
        category = CategoryFactory(name="Electronics", slug="electronics")
        data = CategorySerializer(category).data
        assert data["name"] == "Electronics"
        assert data["slug"] == "electronics"


@pytest.mark.django_db
class TestProductCreateUpdateSerializer:
    def test_valid_data(self):
        category = CategoryFactory()
        supplier = SupplierFactory()
        data = {
            "name": "Test Product",
            "sku": "TST-001",
            "price": "29.99",
            "category": category.pk,
            "supplier": supplier.pk,
        }
        serializer = ProductCreateUpdateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_negative_price(self):
        category = CategoryFactory()
        supplier = SupplierFactory()
        data = {
            "name": "Test Product",
            "sku": "TST-002",
            "price": "-5.00",
            "category": category.pk,
            "supplier": supplier.pk,
        }
        serializer = ProductCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()
        assert "price" in serializer.errors

    def test_duplicate_sku(self):
        ProductFactory(sku="DUPE-001")
        category = CategoryFactory()
        supplier = SupplierFactory()
        data = {
            "name": "Another Product",
            "sku": "DUPE-001",
            "price": "10.00",
            "category": category.pk,
            "supplier": supplier.pk,
        }
        serializer = ProductCreateUpdateSerializer(data=data)
        assert not serializer.is_valid()


class TestPriceUpdateSerializer:
    def test_valid(self):
        serializer = PriceUpdateSerializer(data={"new_price": "25.99"})
        assert serializer.is_valid()

    def test_negative_price(self):
        serializer = PriceUpdateSerializer(data={"new_price": "-1.00"})
        assert not serializer.is_valid()


class TestRestockSerializer:
    def test_valid(self):
        serializer = RestockSerializer(data={"quantity": 10})
        assert serializer.is_valid()

    def test_zero_quantity(self):
        serializer = RestockSerializer(data={"quantity": 0})
        assert not serializer.is_valid()
