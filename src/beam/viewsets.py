from collections import OrderedDict

from django.urls import path, reverse
from django.utils.translation import ugettext_lazy as _

from beam.registry import RegistryMetaClass, default_registry
from .views import CreateView, UpdateView, DetailView, DeleteView, ListView


class ViewSetContext(dict):
    pass


class ContextItemNotFound(Exception):
    pass


class BaseViewSet(metaclass=RegistryMetaClass):
    registry = default_registry
    view_types = []
    context_items = [
        "model",
        "fields",
        "queryset",
        "inline_classes",
        "layout",
        "form_class",
    ]

    model = None
    fields = None
    layout = None
    queryset = None
    inline_classes = None
    form_class = None

    @property
    def links(self):
        links = OrderedDict()
        for view_type in self.get_view_types():
            link = self._get_link(view_type)
            if link:
                links[view_type] = link
        return links

    def _get_url_kwargs(self, view_type):
        return getattr(self, "{}_url_kwargs".format(view_type), [])

    def _get_link(self, view_type):
        url_name = self._get_url_name(view_type)
        url_kwargs = self._get_url_kwargs(view_type)
        verbose_name = getattr(self, "{}_verbose_name".format(view_type), view_type)
        return ViewLink(
            view_type=view_type,
            url_name=url_name,
            verbose_name=verbose_name,
            url_kwargs=url_kwargs,
        )

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

        raise ContextItemNotFound

    def _get_viewset_context(self, view_type):
        viewset_context = ViewSetContext()
        viewset_context["view_type"] = view_type
        viewset_context["viewset"] = self
        for item_name in self.get_context_items():
            try:
                viewset_context[item_name] = self._get_with_generic_fallback(
                    view_type, item_name
                )
            except ContextItemNotFound:
                pass
        return viewset_context

    def _get_view(self, view_type):
        # FIXME handle function based views?
        view_class = getattr(self, "{}_view_class".format(view_type))
        view_kwargs = {}

        if hasattr(view_class, "links"):
            view_kwargs["links"] = self.links

        view = view_class.as_view(**view_kwargs)
        if hasattr(view_class, "viewset_context"):

            def wrapped_view(request, *args, **kwargs):  # FIXME wrap better
                viewset_context = self._get_viewset_context(view_type) or {}
                view.view_initkwargs["viewset_context"] = viewset_context
                return view(request, *args, **kwargs)

            return wrapped_view
        else:
            return view

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
        # FIXME maybe move patterns that contain wildcards to the end?
        for view_type in self.get_view_types():
            urlpatterns.append(self._get_url(view_type))
        return urlpatterns

    def get_view_types(self):
        return self.view_types

    def get_context_items(self):
        return self.context_items


class ListMixin(BaseViewSet):
    list_view_class = ListView
    list_url = ""
    list_verbose_name = _("list")

    list_search_fields = None
    list_paginate_by = 25

    def get_context_items(self):
        return super().get_context_items() + ["list_search_fields", "list_paginate_by"]

    def get_view_types(self):
        return super().get_view_types() + ["list"]


class CreateMixin(BaseViewSet):
    create_view_class = CreateView
    create_url = "create/"
    create_verbose_name = _("create")

    def get_view_types(self):
        return super().get_view_types() + ["create"]


class DetailMixin(BaseViewSet):
    detail_view_class = DetailView
    detail_url = "<str:pk>/"
    detail_url_kwargs = ["pk"]
    detail_verbose_name = _("detail")

    def get_view_types(self):
        return super().get_view_types() + ["detail"]


class UpdateMixin(BaseViewSet):
    update_view_class = UpdateView
    update_url = "<str:pk>/update/"
    update_url_kwargs = ["pk"]
    update_verbose_name = _("update")

    def get_view_types(self):
        return super().get_view_types() + ["update"]


class DeleteMixin(BaseViewSet):
    delete_view_class = DeleteView
    delete_url = "<str:pk>/delete/"
    delete_url_kwargs = ["pk"]
    delete_verbose_name = _("delete")

    def get_view_types(self):
        return super().get_view_types() + ["delete"]


class ViewSet(
    DeleteMixin, UpdateMixin, DetailMixin, CreateMixin, ListMixin, BaseViewSet
):
    pass


class ViewLink:
    def __init__(self, view_type, url_name, verbose_name, url_kwargs):
        self.view_type = view_type
        self.url_name = url_name
        self.verbose_name = verbose_name
        self.url_kwargs = url_kwargs

    def get_url(self, obj=None, extra_kwargs=None):
        if not obj:
            return reverse(self.url_name)

        if not obj and self.url_kwargs:
            return

        kwargs = {kwarg: getattr(obj, kwarg) for kwarg in self.url_kwargs}
        if extra_kwargs:
            kwargs.update(extra_kwargs)

        return reverse(self.url_name, kwargs=kwargs)
