from collections import OrderedDict
from functools import wraps
from logging import getLogger
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Type

import django_filters
from beam.registry import ViewsetMetaClass, default_registry
from django.db.models import Model, QuerySet
from django.forms import Form, ModelForm
from django.urls import path
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views import View

from .actions import Action
from .components import BaseComponent, Component, FormComponent, ListComponent
from .inlines import RelatedInline
from .views import CreateView, DeleteView, DetailView, ListView, UpdateView

logger = getLogger(__name__)


undefined = (
    object()
)  # sentinel value for attributes not defined or overwritten on the viewset


LayoutType = List[List[List[str]]]


class BaseViewSet(metaclass=ViewsetMetaClass):
    registry = default_registry

    model: Model
    fields: List[str]
    layout: LayoutType
    queryset: QuerySet
    inline_classes: List[Type[RelatedInline]] = []
    form_class: Form
    link_layout: List[str]
    _component_classes: Sequence[Tuple[str, Type[Component]]] = []

    def get_component_classes(self) -> Sequence[Tuple[str, Type[Component]]]:
        return self._component_classes

    def _get_components(self) -> Dict[str, Component]:
        components: Dict[str, Component] = OrderedDict()
        for name, component in self.get_component_classes():
            kwargs = self._resolve_component_kwargs(name, component.get_arguments())
            components[name] = component(**kwargs)
        return components

    def _resolve_component_kwargs(self, component_name, arguments: Iterable[str]):
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
        view_kwargs: Dict[str, Any] = {}

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
    list_component = ListComponent
    list_view_class = ListView
    list_url = ""
    list_url_name: str
    list_url_kwargs: List[str] = []
    list_verbose_name = _("list")

    list_sort_fields: List[str]
    list_sort_fields_columns: Mapping[str, str]
    list_search_fields: List[str] = []
    list_paginate_by = 25
    list_item_link_layout = ["update", "detail"]

    list_model: Model
    list_fields: List[str]
    list_layout: LayoutType
    list_queryset: QuerySet
    list_inline_classes: List[RelatedInline]
    list_form_class: ModelForm
    list_permission = "{app_label}.view_{model_name}"
    list_filterset_fields: List[str] = []
    list_filterset_class: Optional[Type[django_filters.FilterSet]] = None
    list_action_classes: List[Type[Action]] = []


class CreateMixin(BaseViewSet):
    create_component = FormComponent
    create_view_class = CreateView
    create_url = "create/"
    create_url_kwargs: List[str] = []
    create_url_name: str
    create_verbose_name = _("create")

    create_model: Model
    create_fields: List[str]
    create_layout: LayoutType
    create_queryset: QuerySet
    create_inline_classes: List[RelatedInline]
    create_form_class: ModelForm
    create_link_layout = ["!create", "!update", "..."]
    create_permission = "{app_label}.add_{model_name}"


class UpdateMixin(BaseViewSet):
    update_component = FormComponent
    update_view_class = UpdateView
    update_url = "<str:pk>/update/"
    update_url_kwargs = ["pk"]
    update_url_name: str
    update_verbose_name = _("update")

    update_model: Model
    update_fields: List[str]
    update_layout: LayoutType
    update_queryset: QuerySet
    update_inline_classes: List[RelatedInline]
    update_form_class: ModelForm
    update_link_layout = ["!create", "!update", "list", "...", "detail"]
    update_permission = "{app_label}.change_{model_name}"


class DetailMixin(BaseViewSet):
    detail_component = Component
    detail_view_class: View = DetailView
    detail_url: str = "<str:pk>/"
    detail_url_name: str
    detail_url_kwargs: List[str] = ["pk"]
    detail_verbose_name = _("detail")

    detail_model: Model
    detail_fields: List[str]
    detail_layout: LayoutType
    detail_queryset: QuerySet
    detail_inline_classes: List[RelatedInline]
    detail_link_layout = ["!detail", "...", "update"]
    detail_permission = "{app_label}.view_{model_name}"


class DeleteMixin(BaseViewSet):
    delete_component = Component
    delete_view_class = DeleteView
    delete_url = "<str:pk>/delete/"
    delete_url_name: str
    delete_url_kwargs = ["pk"]
    delete_verbose_name = _("delete")

    delete_model: Model
    delete_fields: List[str]
    delete_layout: LayoutType
    delete_queryset: QuerySet
    delete_inline_classes: List[RelatedInline]
    delete_link_layout = ["!delete", "..."]
    delete_permission = "{app_label}.delete_{model_name}"


class ViewSet(
    DeleteMixin, UpdateMixin, DetailMixin, CreateMixin, ListMixin, BaseViewSet
):
    pass


__all__ = [
    "LayoutType",
    "undefined",
    "BaseViewSet",
    "ListMixin",
    "CreateView",
    "UpdateMixin",
    "DetailMixin",
    "DeleteMixin",
    "ViewSet",
]
