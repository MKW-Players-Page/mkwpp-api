from django.contrib import admin
from django.contrib.admin.apps import AdminConfig
from django.urls import path


class MKWPPAdminSite(admin.AdminSite):
    site_title = "Mario Kart Wii Players' Page Admin Site"
    index_template = 'timetrials/admin/index.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._custom_views = dict()

    def register_view(self, route=None, title=None):
        def decorator(func):
            if route in self._custom_views:
                raise ValueError(f"Route already in use [{route}]")

            def wrapped(request, *args, **kwargs):
                context = self.each_context(request)
                context = {
                    'title': title or "Custom Page",
                    **context,
                }
                return func(request, context, *args, **kwargs)

            self._custom_views[route] = wrapped

            return wrapped

        return decorator

    def get_urls(self):
        return [
            path(route, self.admin_view(view))
            for (route, view) in self._custom_views.items()
        ] + super().get_urls()


class MKWPPAdminConfig(AdminConfig):
    default_site = 'mkwpp.admin.MKWPPAdminSite'
