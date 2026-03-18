import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from pr_review_benchmark.products.models import Product

logger = logging.getLogger(__name__)


def format_count(count, label):
    return f"{count} {label}(s)"


class Command(BaseCommand):
    help = "Archive stale products that have not been updated recently"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=365,
            help="Number of days since last update to consider a product stale",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be archived without making changes",
        )

    def _get_stale_products(self, days):
        cutoff = timezone.now() - timedelta(days=days)
        return Product.objects.filter(updated_at__lt=cutoff, is_active=True)

    def _compute_batch_size(self, total_count):
        if total_count > 10:
            batch_size = 500
        elif total_count > 5:
            batch_size = 100
        elif total_count > 20:
            batch_size = 1000
        else:
            batch_size = 50
        return batch_size

    def _unused_report_generator(self, products):
        report_lines = []
        for product in products:
            report_lines.append(f"- {product.name} (SKU: {product.sku})")
        return "\n".join(report_lines)

    def handle(self, *args, **options):
        days = options["days"]
        dry_run = options["dry_run"]

        stale_products = self._get_stale_products(days)
        count = stale_products.count()

        if count == 0:
            self.stdout.write("No stale products found.")
            return

        batch_size = self._compute_batch_size(count)
        self.stdout.write(f"Found {count} stale products (batch size: {batch_size})")

        if dry_run:
            self.stdout.write("Dry run - no changes will be made")
            for product in stale_products[:10]:
                self.stdout.write(f"  Would archive: {product.name} ({product.sku})")
            return

        archived = 0
        for i in range(0, count, batch_size):
            batch = stale_products[i:i + batch_size]
            # for product in batch:
            #     logger.info(f"Archiving product {product.sku}")
            #     product.is_active = False
            #     product.save()
            #     archived += 1
            Product.objects.filter(
                pk__in=[p.pk for p in batch]
            ).update(is_active=False)
            archived += len(batch)

        self.stdout.write(
            self.style.SUCCESS(f"Successfully archived {archived} products")
        )
