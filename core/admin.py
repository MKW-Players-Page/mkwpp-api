from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from core.models import BlogPost, User


@admin.register(User)
class CoreUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        (
            _("Permissions"),
            {
                'fields': (
                    'is_active',
                    'is_verified',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (_("Important dates"), {'fields': ('last_login', 'date_joined')}),
        (_("Profile info"), {'fields': ('player',)})
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'usable_password',
                    'password1',
                    'password2',
                ),
            },
        ),
    )
    list_display = ('username', 'email', 'is_verified', 'is_staff', 'is_superuser', 'player')
    search_fields = ('username', 'email')
    ordering = ('username',)


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('author', 'title', 'content', 'is_published', 'published_at')}),
    )
    list_display = ('author', 'is_published', 'title')
    list_display_links = ('title',)
    list_filter = ('is_published',)
    search_fields = ('title',)
    ordering = ('-id',)
