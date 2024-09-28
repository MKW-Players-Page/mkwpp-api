from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    # Make email required and add unique constraint
    email = models.EmailField(_("email address"), unique=True)

    is_verified = models.BooleanField(
        default=False,
        help_text=_("Whether the user completed email verification."),
    )

    # Remove unwanted fields from AbstractUser
    first_name = None
    last_name = None

    def get_full_name(self):
        """Return username."""
        return self.username

    def get_short_name(self):
        """Return username."""
        return self.username

    def __str__(self):
        return self.username
