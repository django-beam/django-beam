from collections import OrderedDict
from functools import wraps
from logging import getLogger
from typing import List, Tuple, Dict

from django.db.models import Model, QuerySet
from django.forms import ModelForm
from django.urls import path
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views import View

from beam.registry import RegistryMetaClass, default_registry
from .components import BaseComponent, Component, FormComponent, ListComponent
from .inlines import RelatedInline
from .views import CreateView, UpdateView, DetailView, DeleteView, ListView

logger = getLogger(__name__)


undefined = (
    object()
)  # sentinel value for attributes not defined or overwritten on the viewset

LayoutType = List[List[List[str]]]


class ContextItemNotFound(Exception):
    pass


class BaseViewSet(metaclass=RegistryMetaClass):
    registry = default_registry

    model: Model = None
    fields = None
    layout = None
    queryset = None
    inline_classes = []
    form_class = None
    link_layout = None

    def get_component_classes(self) -> List[Tuple[str, type(Component)]]:
        return []

    def _get_components(self) -> Dict[str, Component]:
        components = OrderedDict()
        for name, component in self.get_component_classes():
            kwargs = self._resolve_component_kwargs(name, component.get_arguments())
            components[name] = component(**kwargs)
        return components

    def _resolve_component_kwargs(self, component_name, arguments: List[str]):
        component_kwargs = {}

        specific_prefix = "{}_".format(component_name)
        for name in arguments:
            if name in ["name", "viewset"]:  # those are set below
                continue
            specific_value = getattr(self, specific_prefix + name, undefined)

            if specific_value is not undefined:
                component_kwargs[name] = specific_value
                continue

            value = getattr(self, name, undefined)
            if value is not undefined:
                component_kwargs[name] = value
                continue

            # FIXME validate that all context items appear on the viewset
            logger.warning(
                "missing value for {} in component {} of {}".format(
                    name, component_name, self
                )
            )

        component_kwargs["name"] = component_name
        component_kwargs["viewset"] = self

        return component_kwargs

    @cached_property
    def components(self) -> Dict[str, Component]:
        return self._get_components()

    @property
    def links(self) -> Dict[str, BaseComponent]:
        """A list of components that can be linked from within the ui"""
        return self.components

    def _get_view(self, component: Component):
        # FIXME handle function based views?
        view_class = component.view_class
        view_kwargs = {}

        view = view_class.as_view(**view_kwargs)
        if hasattr(view_class, "viewset"):

            @wraps(view)
            def wrapped_view(request, *args, **kwargs):
                view.view_initkwargs["viewset"] = self
                view.view_initkwargs["component"] = component
                return view(request, *args, **kwargs)

            return wrapped_view
        else:
            return view

    def _get_url_pattern(self, component):
        view = self._get_view(component)
        url = component.url
        url_name = component.url_name
        return path(url, view, name=url_name)

    def get_urls(self):
        urlpatterns = []
        # FIXME maybe move patterns that contain wildcards to the end?
        for component in self.components.values():
            urlpatterns.append(self._get_url_pattern(component))
        return urlpatterns


class ListMixin(BaseViewSet):
    list_view_class = ListView
    list_url = ""
    list_url_name = None
    list_url_kwargs = []
    list_verbose_name = _("list")

    list_search_fields = None
    list_paginate_by = 25
    list_item_link_layout = ["update", "detail"]

    list_model: Model = undefined
    list_fields: List[str] = undefined
    list_layout: LayoutType = undefined
    list_queryset: QuerySet = undefined
    list_inline_classes: List[RelatedInline] = undefined
    list_form_class: ModelForm = undefined

    def get_component_classes(self):
        return super().get_component_classes() + [("list", ListComponent)]


class CreateMixin(BaseViewSet):
    create_view_class = CreateView
    create_url = "create/"
    create_url_kwargs = []
    create_url_name = None
    create_verbose_name = _("create")

    create_model: Model = undefined
    create_fields: List[str] = undefined
    create_layout: LayoutType = undefined
    create_queryset: QuerySet = undefined
    create_inline_classes: List[RelatedInline] = undefined
    create_form_class: ModelForm = undefined
    create_link_layout = ["!create", "!update", "..."]

    def get_component_classes(self):
        return super().get_component_classes() + [("create", FormComponent)]


class UpdateMixin(BaseViewSet):
    update_view_class = UpdateView
    update_url = "<str:pk>/update/"
    update_url_kwargs = ["pk"]
    update_url_name = None
    update_verbose_name = _("update")

    update_model: Model = undefined
    update_fields: List[str] = undefined
    update_layout: LayoutType = undefined
    update_queryset: QuerySet = undefined
    update_inline_classes: List[RelatedInline] = undefined
    update_form_class: ModelForm = undefined
    update_link_layout = ["!create", "!update", "list", "...", "detail"]

    def get_component_classes(self):
        return super().get_component_classes() + [("update", FormComponent)]


class DetailMixin(BaseViewSet):
    detail_view_class: View = DetailView
    detail_url: str = "<str:pk>/"
    detail_url_name = None
    detail_url_kwargs: List[str] = ["pk"]
    detail_verbose_name = _("detail")

    detail_model: Model = undefined
    detail_fields: List[str] = undefined
    detail_layout: LayoutType = undefined
    detail_queryset: QuerySet = undefined
    detail_inline_classes: List[RelatedInline] = undefined
    detail_link_layout = ["!detail", "...", "update"]

    def get_component_classes(self):
        return super().get_component_classes() + [("detail", Component)]


class DeleteMixin(BaseViewSet):
    delete_view_class = DeleteView
    delete_url = "<str:pk>/delete/"
    delete_url_name = None
    delete_url_kwargs = ["pk"]
    delete_verbose_name = _("delete")

    delete_model: Model = undefined
    delete_fields: List[str] = undefined
    delete_layout: LayoutType = undefined
    delete_queryset: QuerySet = undefined
    delete_inline_classes: List[RelatedInline] = undefined
    delete_link_layout = ["!delete", "..."]

    def get_component_classes(self):
        return super().get_component_classes() + [("delete", Component)]


class ViewSet(
    DeleteMixin, UpdateMixin, DetailMixin, CreateMixin, ListMixin, BaseViewSet
):
    pass
