from datetime import date

from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class Subscription(models.Model):
    """
    The main subscription model with below fields.
    Constraints: Only 1 subscription allowed per email + city combination.

    :var email: The email address of the user
    :var verified: A boolean flag indicating if the subscription has been verified
    :var temp_token: Temporary token generated for verification
    :var city: The name of the city selected
    :var dominentpol: the name of the dominent pollutant for that city
    :var next_email_date: the date when the next email has to be sent
    :var created_date: the date when this subscription was created
    :var update_date: the date when this subscription was last updated
    :var status: an ENUM if subscription is active or not
    """

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
