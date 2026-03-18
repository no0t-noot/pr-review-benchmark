from django.db import connection, transaction
from django.db.models import F
from django.utils import timezone
from rest_framework import generics, status, viewsets
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


class ProductAnalyticsAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")
        category_id = request.query_params.get("category_id")

        with connection.cursor() as cursor:
            sql = """
                SELECT
                    c.name as category_name,
                    COUNT(p.id) as product_count,
                    AVG(p.price) as avg_price,
                    SUM(p.price * i.quantity) as total_value,
                    MIN(p.price) as min_price,
                    MAX(p.price) as max_price
                FROM products_product p
                JOIN products_category c ON p.category_id = c.id
                LEFT JOIN products_inventory i ON i.product_id = p.id
                WHERE p.is_active = true
            """
            params = []
            if category_id:
                sql += " AND c.id = %s"
                params.append(category_id)
            if date_from:
                sql += " AND p.created_at >= %s"
                params.append(date_from)
            if date_to:
                sql += " AND p.created_at <= %s"
                params.append(date_to)
            sql += " GROUP BY c.name ORDER BY total_value DESC"

            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        results = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            if row_dict["total_value"]:
                margin = float(row_dict["avg_price"]) * 0.3
                row_dict["estimated_margin"] = round(margin * row_dict["product_count"], 2)
            else:
                row_dict["estimated_margin"] = 0
            results.append(row_dict)

        total_products = sum(r["product_count"] for r in results)
        total_value = sum(r["total_value"] or 0 for r in results)

        return Response({
            "categories": results,
            "summary": {
                "total_products": total_products,
                "total_value": float(total_value),
                "category_count": len(results),
            },
        })
