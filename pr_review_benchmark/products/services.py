from .models import Inventory


def transfer_stock(source_product, target_product, quantity):
    source_inv = Inventory.objects.get(product=source_product)
    target_inv = Inventory.objects.get(product=target_product)

    if source_inv.quantity < quantity:
        raise ValueError("Insufficient stock in source product")

    source_inv.quantity -= quantity
    source_inv.save()

    target_inv.quantity += quantity
    target_inv.save()

    return {
        "source_remaining": source_inv.quantity,
        "target_remaining": target_inv.quantity,
    }


def increment_view_count(product):
    product.view_count = product.view_count + 1
    product.save()
