from django.urls import path, reverse

from .views import CreateView, UpdateView, DetailView, DeleteView, ListView


class ViewsetContext(dict):
    pass


class BaseViewSet:
    view_types = []
    context_items = ["model", "fields", "queryset", "view_kwargs", "links"]

    model = None
    fields = None
    queryset = None
    view_kwargs = None

    def get_links(self):
        links = []
        for view_type in self.get_view_types():
            links.append((view_type, self._get_lazy_reverse(view_type)))
        return links

    def _get_lazy_reverse(self, view_type):
        return getattr(self, "{}_reverse".format(view_type))

    def _get_with_generic_fallback(self, view_type, item_name):
        specific_getter_name = "get_{}_{}".format(view_type, item_name)
        specific_attribute_name = "{}_{}".format(view_type, item_name)
        generic_getter_name = "get_{}".format(item_name)
        generic_attribute_name = item_name

        if hasattr(self, specific_getter_name):
            return getattr(self, specific_getter_name)()
        if hasattr(self, specific_attribute_name):
            return getattr(self, specific_attribute_name)
        if hasattr(self, generic_getter_name):
            return getattr(self, generic_getter_name)()
        if hasattr(self, generic_attribute_name):
            return getattr(self, generic_attribute_name)

        raise Exception(
            'No context item "{}" found, define any of {}'.format(
                item_name,
                ", ".join(
                    (
                        generic_attribute_name,
                        generic_getter_name,
                        specific_attribute_name,
                        specific_getter_name,
                    )
                ),
            )
        )

    def _get_viewset_context(self, view_type):
        viewset_context = ViewsetContext()
        viewset_context["view_type"] = view_type
        for item_name in self._get_with_generic_fallback(view_type, "context_items"):
            viewset_context[item_name] = self._get_with_generic_fallback(
                view_type, item_name
            )
        return viewset_context

    def _get_view(self, view_type):
        # FIXME handle function based views?
        view_class = getattr(self, "{}_view_class".format(view_type))
        view_kwargs = self._get_with_generic_fallback(view_type, "view_kwargs") or {}
        if hasattr(view_class, "viewset_context"):
            viewset_context = self._get_viewset_context(view_type) or {}
            view_kwargs["viewset_context"] = viewset_context

        return view_class.as_view(**view_kwargs)

    def _get_url_name(self, view_type):
        return "{}_{}_{}".format(
            self.model._meta.app_label, self.model._meta.model_name, view_type
        )

    def _get_url(self, view_type):
        view = self._get_view(view_type)
        url = getattr(self, "{}_url".format(view_type))
        url_name = self._get_url_name(view_type)
        return path(url, view, name=url_name)

    def get_urls(self):
        urlpatterns = []
        for view_type in self.get_view_types():
            urlpatterns.append(self._get_url(view_type))
        return urlpatterns

    def get_view_types(self):
        return self.view_types


class ListMixin(BaseViewSet):
    list_view_class = ListView
    list_url = ""

    def list_reverse(self):
        return reverse(self._get_url_name("list"))

    def get_view_types(self):
        return super().get_view_types() + ["list"]


class CreateMixin(BaseViewSet):
    create_view_class = CreateView
    create_url = "create/"

    def create_reverse(self):
        return reverse(self._get_url_name("create"))

    def get_view_types(self):
        return super().get_view_types() + ["create"]


class DetailMixin(BaseViewSet):
    detail_view_class = DetailView
    detail_url = "<str:pk>/detail/"

    def detail_reverse(self, obj):
        return reverse(self._get_url_name("detail"), kwargs={"pk": obj.pk})

    def get_view_types(self):
        return super().get_view_types() + ["detail"]


class UpdateMixin(BaseViewSet):
    update_view_class = UpdateView
    update_url = "<str:pk>/update/"

    def update_reverse(self, obj):
        return reverse(self._get_url_name("update"), kwargs={"pk": obj.pk})

    def get_view_types(self):
        return super().get_view_types() + ["update"]


class DeleteMixin(BaseViewSet):
    delete_view_class = DeleteView
    delete_url = "<str:pk>/delete/"

    def delete_reverse(self, obj):
        return reverse(self._get_url_name("delete"), kwargs={"pk": obj.pk})

    def get_view_types(self):
        return super().get_view_types() + ["delete"]


class ViewSet(
    DeleteMixin, UpdateMixin, DetailMixin, CreateMixin, ListMixin, BaseViewSet
):
    pass


class ExportMixin(BaseViewSet):
    export_view_class = NotImplemented
    export_url = "<str:pk>/export/"

    def export_reverse(self, obj=None):
        return reverse(self._get_url_name("export"), kwargs={"pk": obj.pk})

    def get_view_types(self):
        return super().get_view_types() + ["export"]
