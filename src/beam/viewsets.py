from collections import OrderedDict
from functools import wraps
from logging import getLogger
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Type

import django_filters
from django.db.models import Model, QuerySet
from django.forms import Form, ModelForm
from django.urls import path
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views import View

from beam.registry import ViewsetMetaClass, default_registry

from .actions import Action
from .facets import BaseFacet, Facet, FormFacet, ListFacet
from .inlines import RelatedInline
from .types import LayoutType
from .urls import UrlKwargDict
from .views import CreateView, DeleteView, DetailView, ListView, UpdateView

logger = getLogger(__name__)


undefined = (
    object()
)  # sentinel value for attributes not defined or overwritten on the viewset


class BaseViewSet(metaclass=ViewsetMetaClass):
    registry = default_registry

    model: Model
    fields: List[str]
    layout: LayoutType
    queryset: QuerySet
    inline_classes: List[Type[RelatedInline]] = []
    form_class: Form
    link_layout: List[str]
    url_namespace: str = ""

    # we default to change_ because it is a safe default
    permission = "{app_label}.change_{model_name}"

    _facet_classes: Sequence[Tuple[str, Type[Facet]]] = []

    def get_facet_classes(self) -> Sequence[Tuple[str, Type[Facet]]]:
        return self._facet_classes

    def _get_facets(self) -> Dict[str, Facet]:
        facets: Dict[str, Facet] = OrderedDict()
        for name, facet in self.get_facet_classes():
            kwargs = self._resolve_facet_kwargs(name, facet.get_arguments())
            facets[name] = facet(**kwargs)
        return facets

    def _resolve_facet_kwargs(self, facet_name, arguments: Iterable[str]):
        facet_kwargs = {}

        specific_prefix = "{}_".format(facet_name)
        for name in arguments:
            if name in ["name", "viewset"]:  # those are set below
                continue
            specific_value = getattr(self, specific_prefix + name, undefined)

            if specific_value is not undefined:
                facet_kwargs[name] = specific_value
                continue

            value = getattr(self, name, undefined)
            if value is not undefined:
                facet_kwargs[name] = value
                continue

        facet_kwargs["name"] = facet_name
        facet_kwargs["viewset"] = self

        return facet_kwargs

    @cached_property
    def facets(self) -> Dict[str, Facet]:
        return self._get_facets()

    @property
    def links(self) -> Dict[str, BaseFacet]:
        """A list of facets that can be linked from within the ui"""
        return self.facets

    def _get_view(self, facet: Facet):
        # FIXME handle function based views?
        view_class = facet.view_class
        view_kwargs: Dict[str, Any] = {}

        view = view_class.as_view(**view_kwargs)
        if hasattr(view_class, "viewset"):

            @wraps(view)
            def wrapped_view(request, *args, **kwargs):
                view.view_initkwargs["viewset"] = self
                view.view_initkwargs["facet"] = facet
                return view(request, *args, **kwargs)

            return wrapped_view
        else:
            return view

    def _get_url_pattern(self, facet):
        view = self._get_view(facet)
        url = facet.url
        url_name = facet.url_name
        return path(url, view, name=url_name)

    def get_urls(self):
        urlpatterns = []
        facets = list(self.facets.values())

        # move patterns without kwargs to the front
        for facet in facets:
            if not getattr(facet, "url_kwargs", None):
                urlpatterns.append(self._get_url_pattern(facet))

        for facet in facets:
            if getattr(facet, "url_kwargs", None):
                urlpatterns.append(self._get_url_pattern(facet))

        return urlpatterns


class ListMixin(BaseViewSet):
    list_facet = ListFacet
    list_view_class = ListView
    list_url = ""
    list_url_name: str
    list_url_kwargs: UrlKwargDict = {}
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
    list_inline_classes: List[Type[RelatedInline]]
    list_form_class: ModelForm
    list_permission = "{app_label}.view_{model_name}"
    list_filterset_fields: List[str] = []
    list_filterset_class: Optional[Type[django_filters.FilterSet]] = None
    list_action_classes: List[Type[Action]] = []
    list_link_layout = ["create"]


class CreateMixin(BaseViewSet):
    create_facet = FormFacet
    create_view_class = CreateView
    create_url = "create/"
    create_url_kwargs: UrlKwargDict = {}
    create_url_name: str
    create_verbose_name = _("create")

    create_model: Model
    create_fields: List[str]
    create_layout: LayoutType
    create_queryset: QuerySet
    create_inline_classes: List[Type[RelatedInline]]
    create_form_class: ModelForm
    create_link_layout = ["list"]
    create_permission = "{app_label}.add_{model_name}"


class UpdateMixin(BaseViewSet):
    update_facet = FormFacet
    update_view_class = UpdateView
    update_url = "<str:pk>/update/"
    update_url_kwargs: UrlKwargDict = {"pk": "pk"}
    update_url_name: str
    update_verbose_name = _("update")

    update_model: Model
    update_fields: List[str]
    update_layout: LayoutType
    update_queryset: QuerySet
    update_inline_classes: List[Type[RelatedInline]]
    update_form_class: ModelForm
    update_link_layout = ["!create", "!update", "list", "...", "detail"]
    update_permission = "{app_label}.change_{model_name}"


class DetailMixin(BaseViewSet):
    detail_facet = Facet
    detail_view_class: View = DetailView
    detail_url: str = "<str:pk>/"
    detail_url_name: str
    detail_url_kwargs: UrlKwargDict = {"pk": "pk"}
    detail_verbose_name = _("detail")

    detail_model: Model
    detail_fields: List[str]
    detail_layout: LayoutType
    detail_queryset: QuerySet
    detail_inline_classes: List[Type[RelatedInline]]
    detail_link_layout = ["!detail", "...", "update"]
    detail_permission = "{app_label}.view_{model_name}"


class DeleteMixin(BaseViewSet):
    delete_facet = Facet
    delete_view_class = DeleteView
    delete_url = "<str:pk>/delete/"
    delete_url_name: str
    delete_url_kwargs: UrlKwargDict = {"pk": "pk"}
    delete_verbose_name = _("delete")

    delete_model: Model
    delete_fields: List[str]
    delete_layout: LayoutType
    delete_queryset: QuerySet
    delete_inline_classes: List[Type[RelatedInline]]
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
