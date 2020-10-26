import django_filters
from beam import RelatedInline, ViewSet
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
    max_age = django_filters.NumberFilter(lookup_expr="lte", field_name="age")


class DragonflyViewSet(ViewSet):
    inline_classes = [SightingInline]
    model = Dragonfly
    list_search_fields = ["name"]
    fields = ["name", "age"]
    list_filterset_class = DragonflyFilterSet

    extra_component = ExtraComponent
    extra_view_class = ExtraView
    extra_url = "extra/<str:id>/<str:special>/"
    extra_url_kwargs = ["id"]


class SightingViewSet(ViewSet):
    model = Sighting
    fields = ["name", "dragonfly"]
    list_filterset_fields = ["name"]
