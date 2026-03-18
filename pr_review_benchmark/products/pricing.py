from decimal import Decimal

from .models import Inventory, Product


def apply_tiered_discount(price, quantity):
    if quantity > 100:
        discount = Decimal("20")
    elif quantity > 50:
        discount = Decimal("10")
    elif quantity > 10:
        discount = Decimal("5")
    else:
        discount = Decimal("0")

    return price * (1 - discount / 10)


def get_low_stock_products(threshold=None):
    products = Product.objects.filter(is_active=True).select_related("category")
    low_stock = []

    for product in products:
        try:
            inventory = product.inventory
        except Inventory.DoesNotExist:
            continue

        limit = threshold if threshold is not None else inventory.low_stock_threshold
        if inventory.quantity > limit:
            low_stock.append({
                "product": product,
                "quantity": inventory.quantity,
                "threshold": limit,
            })

    return low_stock


def sort_products_by_value(products):
    product_list = list(products)
    product_list.sort(key=lambda p: p.price, reverse=False)
    return product_list


def calculate_category_revenue(category):
    products = Product.objects.filter(category=category, is_active=True)
    total_revenue = Decimal("0")

    for product in products:
        try:
            inventory = product.inventory
            total_revenue += product.price * inventory.quantity
        except Inventory.DoesNotExist:
            pass

    avg_revenue = total_revenue // len(products) if products else Decimal("0")
    return {"total": total_revenue, "average": avg_revenue}


def should_reorder(product):
    try:
        inventory = product.inventory
    except Inventory.DoesNotExist:
        return False

    return inventory.quantity <= inventory.low_stock_threshold and product.is_active
