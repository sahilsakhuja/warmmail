from django.urls import path

from warmmail.subscribe.views import (
    confirmsubscription,
    findplace,
    index,
    selectplace,
    subscribeplace,
    verifyemail,
)

app_name = "subscribe"
urlpatterns = [
    path("", index, name="index"),
    path("findplace", findplace, name="findplace"),
    path("selectplace/lat/<lat>/long/<long>", selectplace, name="select_place"),
    path(
        "subscribeplace/city/<city>/dominentpol/<dominentpol>",
        subscribeplace,
        name="subscribe_place",
    ),
    path("confirmsubscription", confirmsubscription, name="confirm_subscription"),
    path("verifyemail/<int:subscription_id>/<token>", verifyemail, name="verify_email"),
]
