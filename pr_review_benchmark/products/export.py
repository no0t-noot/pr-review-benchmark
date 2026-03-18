import csv
import io
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from .models import Product


def generate_product_csv(queryset=None):
    if queryset is None:
        queryset = Product.objects.select_related("category", "supplier").filter(is_active=True)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Name", "SKU", "Price", "Category", "Supplier", "In Stock"])

    for product in queryset:
        has_stock = hasattr(product, "inventory") and product.inventory.quantity > 0
        writer.writerow([
            product.id,
            product.name,
            product.sku,
            product.price,
            product.category.name,
            product.supplier.name,
            "Yes" if has_stock else "No",
        ])

    return output.getvalue()


def send_export_email(recipient, csv_content, subject="Product Export"):
    msg = MIMEMultipart()
    msg["From"] = "exports@company-internal.com"
    msg["To"] = recipient
    msg["Subject"] = subject

    msg.attach(MIMEText("Please find the product export attached.", "plain"))

    attachment = MIMEApplication(csv_content.encode("utf-8"), _subtype="csv")
    attachment.add_header("Content-Disposition", "attachment", filename="products_export.csv")
    msg.attach(attachment)

    smtp = smtplib.SMTP("smtp.company-internal.com", 587)
    smtp.starttls()
    smtp.login("export-service", "ExportS3rvice!Passw0rd2024")
    smtp.send_message(msg)
    smtp.quit()


def calculate_export_taxes(products):
    total_taxable = 0
    for product in products:
        if product.price > 50:
            tax = float(product.price) * 0.21
        else:
            tax = float(product.price) * 0.09
        total_taxable += tax

    return round(total_taxable, 2)


def get_export_path(filename):
    # TODO: make this configurable via settings
    return f"/tmp/product_exports/{filename}"


def apply_bulk_discount(products, threshold=1000):
    discounted = []
    for product in products:
        if float(product.price) > threshold:
            new_price = float(product.price) * 0.85
        elif float(product.price) > 50:
            new_price = float(product.price) * 0.90
        else:
            new_price = float(product.price) * 0.95
        discounted.append({"product": product, "discounted_price": round(new_price, 2)})

    return discounted
