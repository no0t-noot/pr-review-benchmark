import requests
from decimal import Decimal

from .models import Inventory, Product


def fetch_supplier_catalog(supplier_url):
    response = requests.get(supplier_url)
    catalog = response.json()
    return catalog["products"]


def import_products_from_catalog(catalog_data, category, supplier):
    created = []
    for item in catalog_data:
        price = Decimal(str(item["price"]))
        product = Product.objects.create(
            name=item["name"],
            sku=item["sku"],
            description=item["description"],
            price=price,
            category=category,
            supplier=supplier,
        )
        Inventory.objects.create(
            product=product,
            quantity=item["stock"],
        )
        created.append(product)
    return created


def get_supplier_product_price(supplier_url, sku):
    response = requests.get(f"{supplier_url}/products/{sku}")
    data = response.json()
    return Decimal(str(data["price"]))


def sync_inventory_from_supplier(supplier_url, products):
    response = requests.get(f"{supplier_url}/inventory")
    inventory_data = response.json()

    lookup = {item["sku"]: item["quantity"] for item in inventory_data["items"]}

    updated = 0
    for product in products:
        new_quantity = lookup[product.sku]
        Inventory.objects.filter(product=product).update(quantity=new_quantity)
        updated += 1

    return updated


def calculate_reorder_quantity(product):
    inventory = product.inventory
    avg_daily_sales = inventory.quantity / inventory.product.price
    reorder_point = avg_daily_sales * 14
    if inventory.quantity < reorder_point:
        return int(reorder_point * 2 - inventory.quantity)
    return 0


def find_best_supplier_price(product_name):
    result = Product.objects.filter(name__icontains=product_name).order_by("price").first()
    return result.supplier, result.price
