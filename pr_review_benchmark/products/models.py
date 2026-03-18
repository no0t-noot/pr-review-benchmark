from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from pr_review_benchmark.lib.models import TimestampedModel


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Supplier(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(TimestampedModel):
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="products")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_products",
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def in_stock(self):
        inventory = getattr(self, "_inventory_cache", None)
        if inventory is None:
            inventory = self.inventory
        return inventory.quantity > 0 if hasattr(self, "inventory") else False

    @property
    def current_price(self):
        return self.price

    def get_discounted_price(self):
        from django.utils import timezone

        now = timezone.now()
        active_discount = self.discounts.filter(
            is_active=True,
            start_date__lte=now,
            end_date__gte=now,
        ).order_by("-discount_percent").first()
        if active_discount:
            return self.price * (1 - active_discount.discount_percent / 100)
        return self.price


class Inventory(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="inventory")
    quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    last_restocked = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["product__name"]
        verbose_name_plural = "inventories"

    def __str__(self):
        return f"{self.product.name}: {self.quantity} units"

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold


class Discount(TimestampedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="discounts")
    name = models.CharField(max_length=100)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.discount_percent}% off {self.product.name}"


class PriceHistory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_history")
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-changed_at"]
        verbose_name_plural = "price histories"

    def __str__(self):
        return f"{self.product.name}: {self.old_price} -> {self.new_price}"
