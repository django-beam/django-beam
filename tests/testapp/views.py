import django_filters
from beam import RelatedInline, ViewSet, actions
from beam.actions import DeleteAction
from beam.views import DetailView
from beam.viewsets import Component

from .models import Dragonfly, Sighting


class SightingInline(RelatedInline):
    title = "Title of sightings"
    fields = ["name"]
    model = Sighting
    foreign_key_field = "dragonfly"


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
    inline_classes = [SightingInline]
    model = Dragonfly
    list_search_fields = ["name"]
    fields = ["name", "age"]
    list_filterset_class = DragonflyFilterSet
    list_action_classes = [DeleteAction, DragonFlyUpdateAction]
    list_paginate_by = 5

    extra_component = ExtraComponent
    extra_view_class = ExtraView
    extra_url = "extra/<str:id>/<str:special>/"
    extra_url_kwargs = ["id"]


class SightingViewSet(ViewSet):
    model = Sighting
    fields = ["name", "dragonfly"]
    list_filterset_fields = ["name"]
