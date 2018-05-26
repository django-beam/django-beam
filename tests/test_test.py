from django.db import models
from pytest import mark
from testapp.models import Dragonfly


@mark.django_db
def test_create():
    Dragonfly.objects.create(name="Anna", age="42")
    assert Dragonfly.objects.all().count() == 1
