import factory
from django.utils import timezone

from pr_review_benchmark.lib.factories import BaseMetaFactory

from .models import Category, Inventory, PriceHistory, Product, Supplier


class CategoryFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[Category],
):
    class Meta:
        model = Category
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Category {n}")
    slug = factory.LazyAttribute(lambda obj: obj.name.lower().replace(" ", "-"))
    description = factory.Faker("sentence")


class SupplierFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[Supplier],
):
    class Meta:
        model = Supplier

    name = factory.Faker("company")
    email = factory.Faker("company_email")
    phone = factory.Faker("phone_number")
    address = factory.Faker("address")
    is_active = True


class ProductFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[Product],
):
    class Meta:
        model = Product

    name = factory.Faker("catch_phrase")
    sku = factory.Sequence(lambda n: f"SKU-{n:05d}")
    description = factory.Faker("paragraph")
    price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True, max_value=999)
    category = factory.SubFactory(CategoryFactory)
    supplier = factory.SubFactory(SupplierFactory)
    is_active = True


class InventoryFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[Inventory],
):
    class Meta:
        model = Inventory

    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker("random_int", min=0, max=500)
    low_stock_threshold = 10
    last_restocked = factory.LazyFunction(timezone.now)


class PriceHistoryFactory(
    factory.django.DjangoModelFactory,
    metaclass=BaseMetaFactory[PriceHistory],
):
    class Meta:
        model = PriceHistory

    product = factory.SubFactory(ProductFactory)
    old_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True, max_value=999)
    new_price = factory.Faker("pydecimal", left_digits=3, right_digits=2, positive=True, max_value=999)
