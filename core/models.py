from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from tinymce import models as tinymce_models

from timetrials.models import Player


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

    player = models.OneToOneField(
        Player,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_("Player profile associated with this user."),
    )

    def get_full_name(self):
        """Return username."""
        return self.username

    def get_short_name(self):
        """Return username."""
        return self.username

    def __str__(self):
        return self.username


class BlogPost(models.Model):
    author = models.ForeignKey(User, related_name='blog_posts', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = tinymce_models.HTMLField()
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField()

    def __str__(self):
        return self.title


class Token(models.Model):
    token = models.CharField(max_length=1024)
    salt = models.CharField(max_length=255)
    expiry = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return self.token
