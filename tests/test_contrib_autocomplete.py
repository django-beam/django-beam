from beam import ViewSet
from beam.contrib.autocomplete_light import AutocompleteMixin
from beam.registry import RegistryType
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory, TestCase
from test_views import user_with_perms
from testapp.models import Dragonfly

registry: RegistryType = {}


class AutocompleteDragonflyViewSet(AutocompleteMixin, ViewSet):
    registry = registry

    model = Dragonfly
    fields = ["name", "age"]
    autocomplete_search_fields = ["name"]


class AutocompleteTest(TestCase):
    def test_autocomplete(self):
        request = RequestFactory().get("/", {})
        request.user = user_with_perms(["testapp.view_dragonfly"])

        Dragonfly.objects.create(name="alpha", age=12)
        Dragonfly.objects.create(name="omega", age=99)

        view = AutocompleteDragonflyViewSet()._get_view(
            AutocompleteDragonflyViewSet().components["autocomplete"]
        )

        response = view(request)

        self.assertContains(response, "alpha")
        self.assertContains(response, "omega")

    def test_autocomplete_search(self):
        request = RequestFactory().get("/", {"q": "Al"})
        request.user = user_with_perms(["testapp.view_dragonfly"])

        Dragonfly.objects.create(name="alpha", age=12)
        Dragonfly.objects.create(name="omega", age=99)

        view = AutocompleteDragonflyViewSet()._get_view(
            AutocompleteDragonflyViewSet().components["autocomplete"]
        )

        response = view(request)

        self.assertContains(response, "alpha")
        self.assertNotContains(response, "omega")

    def test_autocomplete_requires_permission(self):
        Dragonfly.objects.create(name="alpha", age=47)

        request = RequestFactory().get("/", {})
        request.user = user_with_perms([])

        view = AutocompleteDragonflyViewSet()._get_view(
            AutocompleteDragonflyViewSet().components["autocomplete"]
        )

        with self.assertRaises(PermissionDenied):
            view(request)
