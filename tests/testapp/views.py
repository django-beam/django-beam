from beam import ViewSet

from .models import Dragonfly


class DragonflyViewSet(ViewSet):
    model = Dragonfly
    fields = ["name"]
