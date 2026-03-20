from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import api_views

router = DefaultRouter()
router.register(r"products", api_views.ProductViewSet, basename="product")
router.register(r"categories", api_views.CategoryViewSet, basename="category")

urlpatterns = [
    path("", include(router.urls)),
    path("products/<int:product_id>/stock/", api_views.StockAPIView.as_view(), name="product-stock"),
    path(
        "products/<int:product_id>/update-price/",
        api_views.UpdatePriceAPIView.as_view(),
        name="product-update-price",
    ),
    path("products/<int:product_id>/restock/", api_views.RestockAPIView.as_view(), name="product-restock"),
    path(
        "products/<int:product_id>/apply-discount/",
        api_views.ApplyDiscountAPIView.as_view(),
        name="product-apply-discount",
    ),
    path("products/cheapest/", api_views.CheapestProductsAPIView.as_view(), name="cheapest-products"),
    path("products/low-stock-alerts/", api_views.LowStockAlertsAPIView.as_view(), name="low-stock-alerts"),
    path("products/inactive/", api_views.InactiveProductsAPIView.as_view(), name="inactive-products"),
    path("categories/revenue/", api_views.CategoryRevenueAPIView.as_view(), name="category-revenue"),
]
