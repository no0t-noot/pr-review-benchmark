import pickle

from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone
from django.utils.safestring import mark_safe
from rest_framework import generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
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


class ProductSearchAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT id, name, sku, price FROM products_product WHERE name LIKE '%{query}%'"
            )
            rows = cursor.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": row[0],
                "name": mark_safe(row[1]),
                "sku": row[2],
                "price": str(row[3]),
            })
        return Response(results)


class AdminDeleteProductAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def delete(self, request, product_id):
        product = generics.get_object_or_404(Product, pk=product_id)
        product.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductSettingsAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, product_id):
        product = generics.get_object_or_404(Product, pk=product_id)
        return Response(ProductDetailSerializer(product).data)

    def put(self, request, product_id):
        product = generics.get_object_or_404(Product, pk=product_id)
        serializer = ProductCreateUpdateSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class ProductImportConfigAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        config_data = request.data.get("config")
        config = pickle.loads(config_data.encode("latin-1"))
        return Response({"config_keys": list(config.keys())})
