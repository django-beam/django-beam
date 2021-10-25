import csv
from typing import Optional

import django_filters
from beam import RelatedInline, ViewSet, actions
from beam.actions import Action, DeleteAction, MassUpdateAction
from beam.inlines import TabularRelatedInline
from beam.urls import request_kwarg
from beam.views import DetailView
from beam.viewsets import Component
from django.db.models import QuerySet
from django.http import HttpResponse

from .models import CascadingSighting, Dragonfly, ProtectedSighting, Sighting


class CsvExportAction(Action):
    name = "csv_export"
    fields = ["id", "name"]
    permission = "{app_label}.view_{model_name}"

    def apply(self, queryset: QuerySet) -> Optional[HttpResponse]:
        values = queryset.values_list(*self.fields)

        response = HttpResponse(content_type="text/csv")
        writer = csv.writer(response)
        writer.writerows(values)
        return response


class NameUpdateAction(MassUpdateAction):
    form_fields = ["name"]


class ProtectedSightingInline(RelatedInline):
    title = "Title of protected sightings"
    detail_template_name = "custom_detail_inline.html"
    form_template_name = "custom_form_inline.html"
    fields = ["name"]
    model = ProtectedSighting
    foreign_key_field = "dragonfly"
    paginate_by = 5
    action_classes = [DeleteAction]


class CascadingSightingInline(TabularRelatedInline):
    title = "Title of cascading sightings"
    fields = ["name"]
    model = CascadingSighting
    foreign_key_field = "dragonfly"
    paginate_by = 5


class SightingInline(RelatedInline):
    title = "Title of sightings"
    fields = ["name"]
    model = Sighting
    foreign_key_field = "dragonfly"
    paginate_by = 5
    filterset_fields = ["name"]
    action_classes = [DeleteAction, NameUpdateAction, CsvExportAction]


class ExtraView(DetailView):
    special_param = None


class ExtraComponent(Component):
    show_link = False


class DragonflyFilterSet(django_filters.FilterSet):
    name = django_filters.CharFilter()
    max_age = django_filters.NumberFilter(lookup_expr="lte", field_name="age")


class DragonFlyUpdateAction(actions.MassUpdateAction):
    form_fields = ["age"]


class DragonflyViewSet(ViewSet):
    inline_classes = [SightingInline, ProtectedSightingInline, CascadingSightingInline]
    model = Dragonfly
    list_search_fields = ["name"]
    fields = ["name", "age"]
    list_filterset_class = DragonflyFilterSet
    list_action_classes = [DeleteAction, DragonFlyUpdateAction]
    list_paginate_by = 5

    extra_component = ExtraComponent
    extra_view_class = ExtraView
    extra_url = "extra/<str:pk>/<str:special>/"
    extra_url_kwargs = {"pk": "id", "special": request_kwarg("special")}


class SightingViewSet(ViewSet):
    model = Sighting
    fields = ["name", "dragonfly"]
    list_filterset_fields = ["name"]
    queryset = Sighting.objects.order_by("pk")
