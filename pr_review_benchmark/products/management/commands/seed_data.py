from decimal import Decimal

from django.core.management.base import BaseCommand

from pr_review_benchmark.products.factories import (
    CategoryFactory,
    InventoryFactory,
    PriceHistoryFactory,
    ProductFactory,
    SupplierFactory,
)


class Command(BaseCommand):
    help = "Seed the database with sample product data"

    def handle(self, *args, **options):
        self.stdout.write("Seeding categories...")
        categories = [
            CategoryFactory(name="Electronics", slug="electronics"),
            CategoryFactory(name="Clothing", slug="clothing"),
            CategoryFactory(name="Home & Garden", slug="home-garden"),
            CategoryFactory(name="Books", slug="books"),
            CategoryFactory(name="Sports & Outdoors", slug="sports-outdoors"),
        ]

        self.stdout.write("Seeding suppliers...")
        suppliers = [
            SupplierFactory(name="TechParts Inc."),
            SupplierFactory(name="Global Fabrics Ltd."),
            SupplierFactory(name="Quality Goods Co."),
        ]

        self.stdout.write("Seeding products with inventory and price history...")
        product_data = [
            ("Wireless Headphones", "SKU-10001", categories[0], suppliers[0], Decimal("79.99")),
            ("USB-C Hub", "SKU-10002", categories[0], suppliers[0], Decimal("45.00")),
            ("Mechanical Keyboard", "SKU-10003", categories[0], suppliers[0], Decimal("129.99")),
            ("27-inch Monitor", "SKU-10004", categories[0], suppliers[0], Decimal("349.99")),
            ("Cotton T-Shirt", "SKU-10005", categories[1], suppliers[1], Decimal("19.99")),
            ("Denim Jeans", "SKU-10006", categories[1], suppliers[1], Decimal("49.99")),
            ("Winter Jacket", "SKU-10007", categories[1], suppliers[1], Decimal("89.99")),
            ("Running Shoes", "SKU-10008", categories[1], suppliers[1], Decimal("74.99")),
            ("Garden Hose", "SKU-10009", categories[2], suppliers[2], Decimal("29.99")),
            ("LED Desk Lamp", "SKU-10010", categories[2], suppliers[2], Decimal("34.99")),
            ("Throw Pillow Set", "SKU-10011", categories[2], suppliers[2], Decimal("24.99")),
            ("Wall Clock", "SKU-10012", categories[2], suppliers[2], Decimal("22.50")),
            ("Python Cookbook", "SKU-10013", categories[3], suppliers[2], Decimal("39.99")),
            ("Design Patterns", "SKU-10014", categories[3], suppliers[2], Decimal("44.99")),
            ("Clean Code", "SKU-10015", categories[3], suppliers[2], Decimal("35.00")),
            ("Data Structures", "SKU-10016", categories[3], suppliers[2], Decimal("42.00")),
            ("Yoga Mat", "SKU-10017", categories[4], suppliers[1], Decimal("25.99")),
            ("Tennis Racket", "SKU-10018", categories[4], suppliers[1], Decimal("59.99")),
            ("Camping Tent", "SKU-10019", categories[4], suppliers[2], Decimal("149.99")),
            ("Hiking Backpack", "SKU-10020", categories[4], suppliers[2], Decimal("69.99")),
        ]

        for name, sku, category, supplier, price in product_data:
            product = ProductFactory(
                name=name,
                sku=sku,
                category=category,
                supplier=supplier,
                price=price,
            )
            InventoryFactory(product=product)
            PriceHistoryFactory(
                product=product,
                old_price=price - Decimal("5.00"),
                new_price=price,
            )

        self.stdout.write(self.style.SUCCESS("Successfully seeded database with 20 products"))
