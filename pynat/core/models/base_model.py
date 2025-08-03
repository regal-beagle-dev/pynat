from django.db import models
from django.utils.timezone import now

from core.models import fields


class BaseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

    def with_deleted(self):
        return super().get_queryset()


class BaseModel(models.Model):
    id = fields.RandomCharField(
        primary_key=True,
        length=12,
        include_alpha=True,
        include_digits=True,
        unique=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects = BaseManager()

    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, *args, **kwargs):
        self.deleted_at = now()
        self.save()

    def delete_forever(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def restore(self):
        self.deleted_at = None
        self.save()
