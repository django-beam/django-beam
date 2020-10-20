from beam.registry import default_registry, unregister
from beam.viewsets import ViewSet
from django.test import TestCase
from testapp.models import Dragonfly, Petaluridae
from testapp.views import DragonflyViewSet


class RegistryTest(TestCase):
    def test_registry_contains_viewset(self):
        self.assertIs(default_registry["testapp"]["dragonfly"], DragonflyViewSet)

    def test_duplicate_registration_warns(self):
        with self.assertWarns(UserWarning):

            class AnotherDragonFlyViewSet(DragonflyViewSet):
                pass

    def test_duplicate_registration_after_unregister_is_okay(self):
        custom_registry = {}

        class OneDragonFlyViewSet(DragonflyViewSet):
            registry = custom_registry

        unregister(custom_registry, Dragonfly)

        class AnotherDragonFlyViewSet(DragonflyViewSet):
            registry = custom_registry

        self.assertIs(custom_registry["testapp"]["dragonfly"], AnotherDragonFlyViewSet)

    def test_unregister_removes_app_and_model(self):
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

    def test_register_with_custom_registry(self):
        custom_registry = {}

        class AnotherDragonFlyViewSet(DragonflyViewSet):
            registry = custom_registry

        self.assertIs(default_registry["testapp"]["dragonfly"], DragonflyViewSet)
        self.assertIs(custom_registry["testapp"]["dragonfly"], AnotherDragonFlyViewSet)
