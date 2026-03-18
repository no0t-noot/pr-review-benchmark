from django.contrib import admin

from .models import Category, Inventory, PriceHistory, Product, Supplier


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name", "email"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "price", "category", "supplier", "is_active"]
    list_filter = ["is_active", "category", "supplier"]
    search_fields = ["name", "sku"]
    raw_id_fields = ["created_by"]


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ["product", "quantity", "low_stock_threshold", "last_restocked"]
    list_filter = ["last_restocked"]
    search_fields = ["product__name"]


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ["product", "old_price", "new_price", "changed_at", "changed_by"]
    list_filter = ["changed_at"]
    search_fields = ["product__name"]
    raw_id_fields = ["changed_by"]
