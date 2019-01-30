from beam.views import DetailView

from beam import ViewSet, RelatedInline

from .models import Dragonfly, Sighting


class SightingInline(RelatedInline):
    title = "Title of sightings"
    fields = ["name"]
    model = Sighting
    foreign_key_field = "dragonfly"


class ExtraView(DetailView):
    special_param = None


class DragonflyViewSet(ViewSet):
    inline_classes = [SightingInline]
    model = Dragonfly
    list_search_fields = ["name"]
    fields = ["name", "age"]

    extra_view_class = ExtraView
    extra_url = "extra/<str:id>/<str:special>/"
    extra_url_kwargs = ["id"]

    def get_view_types(self):
        return super().get_view_types() + ["extra"]
