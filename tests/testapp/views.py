from beam.views import DetailView

from beam import ViewSet, RelatedInline
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


class DragonflyViewSet(ViewSet):
    inline_classes = [SightingInline]
    model = Dragonfly
    list_search_fields = ["name"]
    fields = ["name", "age"]

    extra_component = ExtraComponent
    extra_view_class = ExtraView
    extra_url = "extra/<str:id>/<str:special>/"
    extra_url_kwargs = ["id"]
