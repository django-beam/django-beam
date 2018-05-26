from django.views.generic import CreateView, UpdateView, DetailView, ListView
from django.urls import path


class ViewSet:
    view_types = ["create", "update", "detail", "list"]

    model = None
    fields = None

    create_view_class = CreateView
    update_view_class = UpdateView
    detail_view_class = DetailView
    list_view_class = ListView

    def _get_view(self, view_type):
        view_class = getattr(self, "{}_view_class".format(view_type))
        view_kwargs = {"model": self.model, "fields": self._get_fields(view_type)}
        return view_class.as_view(**view_kwargs)

    def _get_url_name(self, view_type):
        return "{}_{}_{}".format(
            self.model._meta.app_label, self.model._meta.name, view_type
        )

    def _get_url(self, view_type, view):
        if hasattr(view, "pk"):
            url = "<int:pk>/{}".format(view_type)
        else:
            url = view_type

        url_name = self._get_url_name(view_type)

        return path(url, view, name=url_name)

    def get_urls(self):
        urlpatterns = []
        for view_type in self.view_types:
            view = self._get_view(view_type)
            urlpatterns.append(self._get_url(view_type, view))
        return urlpatterns
