from django.db import models
from beam import ViewSet
from pytest import mark
from testapp.models import Dragonfly


class DragonflyViewSet(ViewSet):
    model = Dragonfly
    fields = ["name"]


@mark.django_db
def test_create():
    Dragonfly.objects.create(name="Anna", age="42")
    assert Dragonfly.objects.all().count() == 1


@mark.django_db
def test_get_urls_produces_urls():
    assert len(DragonflyViewSet().get_urls()) == 5
