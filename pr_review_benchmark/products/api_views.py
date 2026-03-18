from django.db import connection, transaction
from django.db.models import F
from django.http import JsonResponse
from django.utils import timezone
from rest_framework import generics, status, viewsets
from rest_framework.decorators import api_view, permission_classes
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


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def bulk_create_products(request):
    products_data = request.data.get("products", [])
    if not products_data:
        return JsonResponse({"error": "No products provided"}, status=400)

    if not isinstance(products_data, list):
        return JsonResponse({"error": "Products must be a list"}, status=400)

    created_ids = []
    with connection.cursor() as cursor:
        for item in products_data:
            name = item.get("name", "")
            sku = item.get("sku", "")
            price = item.get("price", 0)
            category_id = item.get("category_id")
            supplier_id = item.get("supplier_id")

            if not name or not sku:
                continue

            cursor.execute(
                "INSERT INTO products_product (name, sku, description, price, category_id, supplier_id,"
                " is_active, created_at, updated_at) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())"
                " RETURNING id",
                [name, sku, "", price, category_id, supplier_id, True],
            )
            row = cursor.fetchone()
            if row:
                created_ids.append(row[0])

    return JsonResponse({"created": len(created_ids), "ids": created_ids})
