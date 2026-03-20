from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import generics, serializers, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Category, Inventory, PriceHistory, Product
from .serializers import (
    CategorySerializer,
    InventorySerializer,
    PriceUpdateSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    RestockSerializer,
)


class PurchaseSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)


class StockTransferSerializer(serializers.Serializer):
    source_product_id = serializers.IntegerField()
    target_product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        if data["source_product_id"] == data["target_product_id"]:
            raise serializers.ValidationError("Source and target products must be different.")
        return data


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.select_related("category", "supplier").all()

    def get_serializer_class(self):
        if self.action == "list":
            return ProductListSerializer
        if self.action == "retrieve":
            return ProductDetailSerializer
        return ProductCreateUpdateSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class StockAPIView(generics.RetrieveAPIView):
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        product = generics.get_object_or_404(Product, pk=self.kwargs["product_id"])
        return generics.get_object_or_404(Inventory, product=product)


class UpdatePriceAPIView(generics.GenericAPIView):
    serializer_class = PriceUpdateSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, product_id):
        product = generics.get_object_or_404(Product, pk=product_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        old_price = product.price
        new_price = serializer.validated_data["new_price"]

        PriceHistory.objects.create(
            product=product,
            old_price=old_price,
            new_price=new_price,
            changed_by=request.user,
        )

        product.price = new_price
        product.save(update_fields=["price", "updated_at"])

        return Response(
            {"old_price": str(old_price), "new_price": str(new_price)},
            status=status.HTTP_200_OK,
        )


class RestockAPIView(generics.GenericAPIView):
    serializer_class = RestockSerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, product_id):
        product = generics.get_object_or_404(Product, pk=product_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        quantity = serializer.validated_data["quantity"]

        Inventory.objects.filter(product=product).update(
            quantity=F("quantity") + quantity,
            last_restocked=timezone.now(),
        )

        inventory = Inventory.objects.get(product=product)
        return Response(InventorySerializer(inventory).data, status=status.HTTP_200_OK)


class PurchaseAPIView(generics.GenericAPIView):
    """Process a product purchase: validate stock, decrement inventory,
    and track the sale for daily reporting."""

    serializer_class = PurchaseSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, product_id):
        product = generics.get_object_or_404(Product, pk=product_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        requested_quantity = serializer.validated_data["quantity"]

        inventory = Inventory.objects.get(product=product)
        if inventory.quantity < requested_quantity:
            return Response(
                {"error": "Insufficient stock", "available": inventory.quantity},
                status=status.HTTP_400_BAD_REQUEST,
            )

        inventory.quantity -= requested_quantity
        inventory.daily_sales_count = inventory.daily_sales_count + requested_quantity
        inventory.save()

        total_price = product.price * requested_quantity
        return Response(
            {
                "product": product.name,
                "sku": product.sku,
                "quantity_purchased": requested_quantity,
                "unit_price": str(product.price),
                "total_price": str(total_price),
                "remaining_stock": inventory.quantity,
            },
            status=status.HTTP_200_OK,
        )


class StockTransferAPIView(generics.GenericAPIView):
    """Transfer inventory from one product to another, typically used
    when redistributing stock between warehouse locations."""

    serializer_class = StockTransferSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        source_product = generics.get_object_or_404(Product, pk=serializer.validated_data["source_product_id"])
        target_product = generics.get_object_or_404(Product, pk=serializer.validated_data["target_product_id"])
        quantity = serializer.validated_data["quantity"]

        source_inventory = Inventory.objects.get(product=source_product)
        target_inventory = Inventory.objects.get(product=target_product)

        if source_inventory.quantity < quantity:
            return Response(
                {"error": "Insufficient stock in source product", "available": source_inventory.quantity},
                status=status.HTTP_400_BAD_REQUEST,
            )

        source_inventory.quantity -= quantity
        source_inventory.save()

        target_inventory.quantity += quantity
        target_inventory.save()

        return Response(
            {
                "source": {"product": source_product.name, "remaining_stock": source_inventory.quantity},
                "target": {"product": target_product.name, "new_stock": target_inventory.quantity},
                "transferred": quantity,
            },
            status=status.HTTP_200_OK,
        )
