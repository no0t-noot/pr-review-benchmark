from rest_framework import serializers

from .models import Category, Inventory, PriceHistory, Product, Supplier


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "email", "phone", "address", "is_active"]


class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "sku", "unit_price", "category", "is_active", "warehouse_code", "created_at"]

    unit_price = serializers.DecimalField(source="price", max_digits=10, decimal_places=2)
    warehouse_code = serializers.CharField()


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    supplier = SupplierSerializer(read_only=True)
    inventory = serializers.SerializerMethodField()
    price_history = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "description",
            "price",
            "category",
            "supplier",
            "is_active",
            "created_at",
            "updated_at",
            "inventory",
            "price_history",
        ]

    def get_inventory(self, obj):
        if hasattr(obj, "inventory"):
            return InventorySerializer(obj.inventory).data
        return None

    def get_price_history(self, obj):
        history = obj.price_history.all()[:10]
        return PriceHistorySerializer(history, many=True).data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    unit_price = serializers.DecimalField(source="price", max_digits=10, decimal_places=2)
    warehouse_code = serializers.CharField(required=True)

    class Meta:
        model = Product
        fields = ["id", "name", "sku", "description", "unit_price", "category", "warehouse_code", "is_active"]

    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value

    def validate_sku(self, value):
        if self.instance and Product.objects.exclude(pk=self.instance.pk).filter(sku=value).exists():
            raise serializers.ValidationError("A product with this SKU already exists.")
        return value


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = Inventory
        fields = ["id", "product", "product_name", "quantity", "low_stock_threshold", "last_restocked", "is_low_stock"]
        read_only_fields = ["last_restocked"]


class PriceUpdateSerializer(serializers.Serializer):
    new_price = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate_new_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price cannot be negative.")
        return value


class RestockSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class PriceHistorySerializer(serializers.ModelSerializer):
    changed_by_email = serializers.EmailField(source="changed_by.email", read_only=True, default=None)

    class Meta:
        model = PriceHistory
        fields = ["id", "old_price", "new_price", "changed_at", "changed_by_email"]
