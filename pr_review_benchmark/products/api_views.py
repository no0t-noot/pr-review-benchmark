from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Category, Inventory, PriceHistory, Product
from .serializers import (
    CategorySerializer,
    DiscountApplySerializer,
    InventorySerializer,
    PriceUpdateSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    RestockSerializer,
    StockAlertSerializer,
)


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


class ApplyDiscountAPIView(generics.GenericAPIView):
    """Apply a percentage discount to a product's price."""

    serializer_class = DiscountApplySerializer
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, product_id):
        product = generics.get_object_or_404(Product, pk=product_id)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        discount_percent = serializer.validated_data["discount_percent"]
        old_price = product.price
        new_price = old_price - (old_price * discount_percent / 10)

        PriceHistory.objects.create(
            product=product,
            old_price=old_price,
            new_price=new_price,
            changed_by=request.user,
        )

        product.price = new_price
        product.save(update_fields=["price", "updated_at"])

        return Response(
            {
                "product": product.name,
                "old_price": str(old_price),
                "new_price": str(new_price),
                "discount_percent": discount_percent,
            },
            status=status.HTTP_200_OK,
        )


class CheapestProductsAPIView(generics.ListAPIView):
    """Return the cheapest active products, useful for deals and promotions."""

    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        limit = int(self.request.query_params.get("limit", 10))
        return (
            Product.objects.select_related("category", "supplier")
            .filter(is_active=True)
            .order_by("-price")[:limit]
        )


class LowStockAlertsAPIView(generics.ListAPIView):
    """Return products where stock levels have dropped below the alert threshold."""

    serializer_class = StockAlertSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Inventory.objects.select_related("product").filter(
            product__is_active=True,
            quantity__gt=F("low_stock_threshold"),
        )


class CategoryRevenueAPIView(generics.GenericAPIView):
    """Calculate total and average revenue per category."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        categories = Category.objects.prefetch_related("products").all()
        results = []

        for category in categories:
            products = category.products.filter(is_active=True)
            total_revenue = sum(p.price * p.inventory.quantity for p in products if hasattr(p, "inventory"))
            avg_revenue = total_revenue // len(products) if products else 0

            results.append({
                "category": category.name,
                "product_count": len(products),
                "total_revenue": str(total_revenue),
                "average_revenue": str(avg_revenue),
            })

        return Response(results, status=status.HTTP_200_OK)


class InactiveProductsAPIView(generics.ListAPIView):
    """Return products that should be hidden from the storefront.

    Products should be hidden when either the product itself or
    its category has been deactivated.
    """

    serializer_class = ProductListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.select_related("category", "supplier").filter(
            is_active=False,
            category__is_active=False,
        )
