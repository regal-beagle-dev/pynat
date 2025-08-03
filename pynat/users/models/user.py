from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from pynat.core.models import BaseModel


class User(AbstractUser, BaseModel):
    username = models.CharField(_("Username"), null=False, max_length=150)
    name = models.CharField(_("Name of User"), blank=True, max_length=255)
    email = models.EmailField(_("Email"), blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["username"],
                name="unique_username_when_not_deleted",
                condition=models.Q(deleted_at__isnull=True),
            ),
            models.UniqueConstraint(
                fields=["email"],
                name="unique_email_when_not_deleted",
                condition=models.Q(deleted_at__isnull=True),
            ),
        ]

    def get_absolute_url(self) -> str:
        return reverse("users:detail", kwargs={"username": self.username})
