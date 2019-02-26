import pytest
from beam.viewsets import ViewSet
from beam.registry import unregister, default_registry

from testapp.models import Dragonfly, Petaluridae
from testapp.views import DragonflyViewSet


def test_registry_contains_viewset():
    assert default_registry["testapp"]["dragonfly"] is DragonflyViewSet


def test_duplicate_registration_errors():
    with pytest.raises(Exception):

        class AnotherDragonFlyViewSet(DragonflyViewSet):
            pass


def test_duplicate_registration_after_unregister_is_okay():
    custom_registry = {}

    class OneDragonFlyViewSet(DragonflyViewSet):
        registry = custom_registry

    unregister(custom_registry, Dragonfly)

    class AnotherDragonFlyViewSet(DragonflyViewSet):
        registry = custom_registry

    assert custom_registry["testapp"]["dragonfly"] is AnotherDragonFlyViewSet


def test_unregister_removes_app_and_model():
    custom_registry = {}

    class CustomDragonflyViewSet(ViewSet):
        registry = custom_registry
        model = Dragonfly

    class PetaluridaeViewSet(ViewSet):
        registry = custom_registry
        model = Petaluridae

    unregister(custom_registry, Dragonfly)

    assert "dragonfly" not in custom_registry["testapp"]

    unregister(custom_registry, Petaluridae)

    assert "testapp" not in custom_registry


def test_register_with_custom_registry():
    custom_registry = {}

    class AnotherDragonFlyViewSet(DragonflyViewSet):
        registry = custom_registry

    assert default_registry["testapp"]["dragonfly"] is DragonflyViewSet
    assert custom_registry["testapp"]["dragonfly"] is AnotherDragonFlyViewSet
