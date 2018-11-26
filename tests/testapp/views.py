from beam import ViewSet, RelatedInline

from .models import Dragonfly, Sighting


class SightingInline(RelatedInline):
    title = "Title of sightings"
    fields = ["name"]
    model = Sighting
    foreign_key_field = "dragonfly"


class DragonflyViewSet(ViewSet):
    inline_classes = [SightingInline]
    model = Dragonfly
    list_search_fields = ["name"]
    fields = ["name", "age"]
