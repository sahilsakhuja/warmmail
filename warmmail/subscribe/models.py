from datetime import date

from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class Subscription(models.Model):

    email = models.EmailField()
    verified = models.BooleanField(default=False)
    temp_token = models.CharField(max_length=24)
    city = models.CharField(max_length=100)
    dominentpol = models.CharField(max_length=100)
    next_email_date = models.DateTimeField(default=date.today())
    created_date = models.DateTimeField(default=date.today())
    update_date = models.DateTimeField(default=date.today())

    class Meta:
        unique_together = (
            "email",
            "city",
        )

    class Status(models.TextChoices):
        ACTIVE = "A", _("Active")
        INACTIVE = "I", _("Inactive")

    status = models.CharField(
        max_length=1, choices=Status.choices, default=Status.ACTIVE
    )

    def __str__(self):
        return self.email + " -> " + self.city
