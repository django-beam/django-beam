from django.urls import path

from .views import CreateView, UpdateView, DetailView, DeleteView, ListView


def _view_accepts(view_class, attribute_name):
    return hasattr(view_class, attribute_name)


class ViewSet:
    view_types = ["create", "update", "detail", "list", "delete"]

    model = None
    fields = None

    create_view_class = CreateView
    update_view_class = UpdateView
    detail_view_class = DetailView
    list_view_class = ListView
    delete_view_class = DeleteView

    def _get_fields(self, view_type):
        specific_getter_name = "get_{}_fields".format(view_type)
        if hasattr(self, specific_getter_name):
            return getattr(self, specific_getter_name)()
        return self.get_fields()

    def get_fields(self):
        return self.fields

    def _get_view_kwargs(self, view_type, view_class):
        kwargs = {}
        if _view_accepts(view_class, "model"):
            kwargs["model"] = self.model
        if _view_accepts(view_class, "fields"):  # FIXME generalize this
            kwargs["fields"] = self._get_fields(view_type)
        return kwargs

    def _get_view_class(self, view_type):
        return getattr(self, "{}_view_class".format(view_type))

    def _get_view(self, view_type, view_class):
        view_kwargs = self._get_view_kwargs(view_type, view_class)
        return view_class.as_view(**view_kwargs)

    def _get_url_name(self, view_type):
        return "{}_{}_{}".format(
            self.model._meta.app_label, self.model._meta.model_name, view_type
        )

    def _get_url(self, view_type):
        view_class = self._get_view_class(view_type)

        if hasattr(view_class, "pk_url_kwarg"):
            url = "<int:{}>/{}/".format(getattr(view_class, "pk_url_kwarg"), view_type)
        else:
            url = view_type + "/"

        view = self._get_view(view_type, view_class)

        url_name = self._get_url_name(view_type)

        return path(url, view, name=url_name)

    def get_urls(self):
        urlpatterns = []
        for view_type in self.view_types:
            urlpatterns.append(self._get_url(view_type))
        return urlpatterns
