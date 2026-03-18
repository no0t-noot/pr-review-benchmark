from django.db.models import Avg, Count, F, Sum
from django.views.generic import DetailView, ListView, TemplateView

from .models import Category, Inventory, Product


class ProductListView(ListView):
    model = Product
    template_name = "products/product_list.html"
    context_object_name = "products"
    paginate_by = 12

    def get_queryset(self):
        return Product.objects.select_related("category", "supplier").filter(is_active=True)


class ProductDetailView(DetailView):
    model = Product
    template_name = "products/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.select_related("category", "supplier").prefetch_related("price_history")


class DashboardView(TemplateView):
    template_name = "products/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["total_products"] = Product.objects.filter(is_active=True).count()
        context["total_categories"] = Category.objects.count()
        context["avg_price"] = Product.objects.filter(is_active=True).aggregate(avg=Avg("price"))["avg"]
        context["low_stock_count"] = Inventory.objects.filter(quantity__lte=F("low_stock_threshold")).count()
        context["category_stats"] = Category.objects.annotate(
            product_count=Count("products"),
            total_value=Sum("products__price"),
        ).order_by("-product_count")
        return context
