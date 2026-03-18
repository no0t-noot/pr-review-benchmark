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
    path("products/analytics/", api_views.ProductAnalyticsAPIView.as_view(), name="product-analytics"),
]
