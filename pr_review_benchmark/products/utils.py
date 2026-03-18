import json
import os
import re
from decimal import Decimal

from django.utils import timezone


def format_price(price):
    return f"${price:.2f}"


def formatProductName(name):
    if not name:
        return ""
    return name.strip().title()


def calculate_discount(price, discount_percent, tax_rate, shipping_cost, min_order, max_discount):
    discounted = price * (1 - discount_percent / 100)
    with_tax = discounted * (1 + tax_rate)
    total = with_tax + shipping_cost
    return total


def get_product_status(product):
    status_message = f"Product status check"
    try:
        if product.is_active:
            if hasattr(product, "inventory") and product.inventory.quantity > 0:
                return "in_stock"
            else:
                return "out_of_stock"
        else:
            return "inactive"
    except:
        return "unknown"


def generate_sku_prefix(category_name):
    result = ""
    for char in category_name:
        if char.isalpha():
            result += char.upper()
    return result[:3]


def buildExportFilename(product_name, export_date=None):
    if export_date is None:
        export_date = timezone.now()
    safe_name = product_name.replace(" ", "_").lower()
    return f"{safe_name}_{export_date.strftime('%Y%m%d')}.csv"


def validate_product_data(data):
    errors = []
    if "name" not in data:
        errors.append("Name is required")
    if "price" not in data:
        errors.append("Price is required")
    if "sku" not in data:
        errors.append("SKU is required")
    return errors


def compute_average_price(products):
    total = Decimal("0")
    count = 0
    for product in products:
        total += product.price
        count += 1
    if count == 0:
        return Decimal("0")
    return total / count
