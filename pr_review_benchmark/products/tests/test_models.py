from decimal import Decimal

import pytest

from pr_review_benchmark.products.factories import (
    CategoryFactory,
    InventoryFactory,
    PriceHistoryFactory,
    ProductFactory,
    SupplierFactory,
)


@pytest.mark.django_db
class TestCategory:
    def test_str(self):
        category = CategoryFactory(name="Electronics")
        assert str(category) == "Electronics"

    def test_ordering(self):
        CategoryFactory(name="Zebra")
        CategoryFactory(name="Alpha")
        from pr_review_benchmark.products.models import Category
        names = list(Category.objects.values_list("name", flat=True))
        assert names == sorted(names)


@pytest.mark.django_db
class TestSupplier:
    def test_str(self):
        supplier = SupplierFactory(name="Acme Corp")
        assert str(supplier) == "Acme Corp"


@pytest.mark.django_db
class TestProduct:
    def test_str(self):
        product = ProductFactory(name="Widget", sku="SKU-001")
        assert str(product) == "Widget (SKU-001)"

    def test_current_price(self):
        product = ProductFactory(price=Decimal("19.99"))
        assert product.current_price == Decimal("19.99")

    def test_in_stock_with_inventory(self):
        product = ProductFactory()
        InventoryFactory(product=product, quantity=10)
        product.refresh_from_db()
        assert product.in_stock is True

    def test_not_in_stock_with_zero_inventory(self):
        product = ProductFactory()
        InventoryFactory(product=product, quantity=0)
        product.refresh_from_db()
        assert product.in_stock is False


@pytest.mark.django_db
class TestInventory:
    def test_str(self):
        product = ProductFactory(name="Widget")
        inventory = InventoryFactory(product=product, quantity=42)
        assert str(inventory) == "Widget: 42 units"

    def test_is_low_stock(self):
        inventory = InventoryFactory(quantity=5, low_stock_threshold=10)
        assert inventory.is_low_stock is True

    def test_is_not_low_stock(self):
        inventory = InventoryFactory(quantity=50, low_stock_threshold=10)
        assert inventory.is_low_stock is False


@pytest.mark.django_db
class TestPriceHistory:
    def test_str(self):
        product = ProductFactory(name="Widget")
        history = PriceHistoryFactory(product=product, old_price=Decimal("10.00"), new_price=Decimal("15.00"))
        assert str(history) == "Widget: 10.00 -> 15.00"
