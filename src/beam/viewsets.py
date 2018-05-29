from collections import OrderedDict

from django.urls import path, reverse, NoReverseMatch
from django.utils.translation import ugettext_lazy as _


from .views import CreateView, UpdateView, DetailView, DeleteView, ListView


class ViewsetContext(dict):
    pass


class ContextItemNotFound(Exception):
    pass


def register(registry, model, viewset):
    app_label = model._meta.app_label
    model_name = model._meta.model_name

    app_registry = registry.setdefault(app_label, {})
    if model_name in app_registry:
        raise Exception(
            "Duplicate registration of {} for app label {} with model {}, "
            "beam.viewsets.unregister the existing viewset first.".format(
                viewset, app_label, registry
            )
        )
    app_registry[model_name] = viewset


def unregister(registry, model):
    app_label = model._meta.app_label
    model_name = model._meta.model_name

    if app_label not in registry:
        return

    app_registry = registry[app_label]

    if model_name not in app_registry:
        return

    app_registry.pop(model_name)

    if not app_registry:
        registry.pop(app_label)


class RegistryMetaClass(type):

    def __new__(cls, name, bases, namespace, **kwds):
        result = type.__new__(cls, name, bases, dict(namespace))

        if result.registry is not None and result.model is not None:
            register(result.registry, result.model, result)

        return result


default_registry = {}


class BaseViewSet(metaclass=RegistryMetaClass):
    registry = default_registry
    view_types = []
    context_items = ["model", "fields", "queryset"]

    model = None
    fields = None
    queryset = None

    @property
    def links(self):
        links = OrderedDict()
        for view_type in self.get_view_types():
            links[view_type] = self._get_link(view_type)
        return links

    def _get_link(self, view_type):
        resolve_url = getattr(
            self,
            "{}_resolve_url".format(view_type),
            self._get_default_resolve_url(view_type),
        )

        verbose_name = getattr(self, "{}_verbose_name".format(view_type), view_type)

        return ViewLink(
            view_type=view_type, resolve_url=resolve_url, verbose_name=verbose_name
        )

    def _get_default_resolve_url(self, view_type):
        url_name = self._get_url_name(view_type)

        def resolve_url(obj=None):
            if obj:
                try:
                    return reverse(url_name, kwargs={"pk": obj.pk})
                except NoReverseMatch:
                    pass
            return reverse(url_name)

        return resolve_url

    def _get_with_generic_fallback(self, view_type, item_name, request):
        specific_getter_name = "get_{}_{}".format(view_type, item_name)
        specific_attribute_name = "{}_{}".format(view_type, item_name)
        generic_getter_name = "get_{}".format(item_name)
        generic_attribute_name = item_name

        if hasattr(self, specific_getter_name):
            return getattr(self, specific_getter_name)(request)
        if hasattr(self, specific_attribute_name):
            return getattr(self, specific_attribute_name)
        if hasattr(self, generic_getter_name):
            return getattr(self, generic_getter_name)(request)
        if hasattr(self, generic_attribute_name):
            return getattr(self, generic_attribute_name)

        raise ContextItemNotFound

    def _get_viewset_context(self, view_type, request):
        viewset_context = ViewsetContext()
        viewset_context["view_type"] = view_type
        for item_name in self._get_with_generic_fallback(
            view_type, "context_items", request
        ):
            try:
                viewset_context[item_name] = self._get_with_generic_fallback(
                    view_type, item_name, request
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
                viewset_context = self._get_viewset_context(view_type, request) or {}
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
        for view_type in self.get_view_types():
            urlpatterns.append(self._get_url(view_type))
        return urlpatterns

    def get_view_types(self):
        return self.view_types


class ListMixin(BaseViewSet):
    list_view_class = ListView
    list_url = ""
    list_verbose_name = _("list")

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
    detail_verbose_name = _("detail")

    def get_view_types(self):
        return super().get_view_types() + ["detail"]


class UpdateMixin(BaseViewSet):
    update_view_class = UpdateView
    update_url = "<str:pk>/update/"
    update_verbose_name = _("update")

    def get_view_types(self):
        return super().get_view_types() + ["update"]


class DeleteMixin(BaseViewSet):
    delete_view_class = DeleteView
    delete_url = "<str:pk>/delete/"
    delete_verbose_name = _("delete")

    def get_view_types(self):
        return super().get_view_types() + ["delete"]


class ViewSet(
    DeleteMixin, UpdateMixin, DetailMixin, CreateMixin, ListMixin, BaseViewSet
):
    pass


class ViewLink:

    def __init__(self, view_type, resolve_url, verbose_name):
        self.view_type = view_type
        self.resolve_url = resolve_url
        self.verbose_name = verbose_name

    def get_url(self, obj=None):
        return self.resolve_url(obj=obj)
