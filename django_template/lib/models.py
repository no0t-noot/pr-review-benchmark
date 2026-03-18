import uuid

from django.db import models
from django.utils.translation import gettext as _


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True, db_index=True)

    class Meta:
        abstract = True


class UUIDModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True, unique=True)

    class Meta:
        abstract = True


class OrderableModel(models.Model):
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ["order"]
