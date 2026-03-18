from django.db import transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Category, Discount, Inventory, PriceHistory, Product
from .serializers import (
    CategorySerializer,
    DiscountSerializer,
    InventorySerializer,
    PriceUpdateSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    RestockSerializer,
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


class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.select_related("product").all()
    serializer_class = DiscountSerializer
    permission_classes = [IsAuthenticated]
