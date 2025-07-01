from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.http.response import HttpResponse
from django.test import RequestFactory, TestCase
from django.test.utils import override_settings
from django.urls import include, path
from reversion import is_registered, set_comment
from reversion.models import Version
from test_views import user_with_perms
from testapp.models import Dragonfly, Petaluridae, Sighting

from beam import RelatedInline
from beam.contrib.reversion.viewsets import VersionViewSet
from beam.registry import RegistryType

registry: RegistryType = {}


class GetResponse:
    def __call__(self):
        return HttpResponse()


class SightingInline(RelatedInline):
    title = "Title of sightings"
    fields = ["name"]
    model = Sighting
    foreign_key_field = "dragonfly"


class VersionedDragonflyViewSet(VersionViewSet):
    registry = registry

    inline_classes = [SightingInline]
    model = Dragonfly
    list_search_fields = ["name"]
    fields = ["name", "age"]


urlpatterns = [
    path("dragonfly/", include(VersionedDragonflyViewSet().get_urls())),
]

VersionedDragonflyViewSet()


class RegistrationTest(TestCase):
    def test_versioned_view_set_models_are_registered(self):
        self.assertTrue(is_registered(Dragonfly))

    def test_inlines_of_versioned_view_set_models_are_registered(self):
        self.assertTrue(is_registered(Sighting))

    def test_unrelated_models_are_not_registered(self):
        self.assertFalse(is_registered(Petaluridae))


class ReversionViewTest(TestCase):
    # FIXME: this should probably be a regular webtest with the urlconf above
    def test_using_create_view_creates_a_revision(self):
        user = user_with_perms(["testapp.add_dragonfly"])
        create_view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["create"]
        )

        request = RequestFactory().post(
            "/dragonfly/create/",
            data={
                "name": "versionfly",
                "age": 81,
                "sighting_set-TOTAL_FORMS": 1,
                "sighting_set-INITIAL_FORMS": 0,
                "sighting_set-MIN_NUM_FORMS": 0,
                "sighting_set-MAX_NUM_FORMS": 10,
                "sighting_set-0-name": "Tokyo",
            },
        )
        request.user = user

        middleware = SessionMiddleware(get_response=GetResponse())
        middleware.process_request(request)
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        response = create_view(request)

        self.assertEqual(response.status_code, 302)

        fly = Dragonfly.objects.get()
        fly_version = Version.objects.get_for_object_reference(Dragonfly, fly.pk).get()

        self.assertEqual(fly_version.object.name, "versionfly")
        self.assertEqual(fly_version.field_dict["name"], "versionfly")
        self.assertEqual(fly_version.revision.user, user)
        self.assertEqual(fly_version.revision.comment, "create")

        sighting_version = Version.objects.get_for_object_reference(
            Sighting, fly.sighting_set.get().pk
        ).get()

        self.assertEqual(sighting_version.field_dict["name"], "Tokyo")

    def test_using_update_view_creates_a_revision(self):
        user = user_with_perms(["testapp.change_dragonfly"])
        alpha = Dragonfly.objects.create(name="alpha", age=47)

        update_view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["update"]
        )

        request = RequestFactory().post(
            "/dragonfly/update/{}/".format(alpha.pk),
            data={
                "name": "beta",
                "age": 81,
                "sighting_set-TOTAL_FORMS": 0,
                "sighting_set-INITIAL_FORMS": 0,
                "sighting_set-MIN_NUM_FORMS": 0,
                "sighting_set-MAX_NUM_FORMS": 10,
            },
        )
        request.user = user
        middleware = SessionMiddleware(get_response=GetResponse())
        middleware.process_request(request)
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)

        response = update_view(request, pk=alpha.pk)

        self.assertEqual(response.status_code, 302)

        fly_version = Version.objects.get_for_object_reference(
            Dragonfly, alpha.pk
        ).latest("revision__date_created")

        self.assertEqual(fly_version.object.name, "beta")
        self.assertEqual(fly_version.field_dict["name"], "beta")
        self.assertEqual(fly_version.revision.user, user)
        self.assertEqual(fly_version.revision.comment, "update")

    @override_settings(ROOT_URLCONF=__name__)
    def test_revision_is_visible_in_list(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)

        request = RequestFactory().get("/", {})
        request.user = user_with_perms(["testapp.view_dragonfly"])

        with VersionedDragonflyViewSet().create_revision(request):
            set_comment("number one")
            alpha.save()

        with VersionedDragonflyViewSet().create_revision(request):
            set_comment("number two")
            alpha.save()

        with VersionedDragonflyViewSet().create_revision(request):
            set_comment("number three")
            alpha.save()

        self.assertEqual(
            Version.objects.get_for_object_reference(Dragonfly, alpha.pk).count(), 3
        )

        view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["version_list"]
        )

        response = view(request, pk=alpha.pk)

        self.assertContains(response, "number one")
        self.assertContains(response, "number two")
        self.assertContains(response, "number three")

    def test_version_list_requires_view_permission(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)

        request = RequestFactory().get("/", {})
        request.user = user_with_perms([])

        with VersionedDragonflyViewSet().create_revision(request):
            set_comment("number one")
            alpha.save()

        view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["version_list"]
        )

        with self.assertRaises(PermissionDenied):
            view(request, pk=alpha.pk)

    @override_settings(ROOT_URLCONF=__name__)
    def test_show_detail_from_previous_version(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        sighting = Sighting.objects.create(name="Berlin", dragonfly=alpha)

        request = RequestFactory().get("/", {})
        request.user = user_with_perms(["testapp.view_dragonfly"])

        with VersionedDragonflyViewSet().create_revision(request):
            alpha.save()

        version = Version.objects.get_for_object_reference(Dragonfly, alpha.pk).latest(
            "revision__date_created"
        )

        alpha.name = "beta"
        alpha.save()

        sighting.name = "Tokyo"
        sighting.save()

        detail_view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["detail"]
        )
        detail_page = detail_view(request, pk=alpha.pk)

        self.assertContains(detail_page, "beta")
        self.assertContains(detail_page, "Tokyo")

        version_view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["version_detail"]
        )
        version_page = version_view(request, pk=alpha.pk, version_id=version.pk)

        self.assertContains(version_page, "alpha")
        self.assertContains(version_page, "Berlin")

        self.assertNotContains(version_page, "beta")
        self.assertNotContains(version_page, "Tokyo")

    def test_version_detail_requires_view_perm(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        Sighting.objects.create(name="Berlin", dragonfly=alpha)

        request = RequestFactory().get("/", {})
        request.user = user_with_perms([])

        with VersionedDragonflyViewSet().create_revision(request):
            alpha.save()

        Version.objects.get_for_object_reference(Dragonfly, alpha.pk).latest(
            "revision__date_created"
        )
        detail_view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["detail"]
        )
        with self.assertRaises(PermissionDenied):
            detail_view(request, pk=alpha.pk)

    def test_revert_to_previous_version(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        sighting = Sighting.objects.create(name="Berlin", dragonfly=alpha)

        request = RequestFactory().post("/", {})
        request.user = user_with_perms(["testapp.change_dragonfly"])
        SessionMiddleware(get_response=GetResponse()).process_request(request)
        MessageMiddleware(get_response=GetResponse()).process_request(request)

        with VersionedDragonflyViewSet().create_revision(request):
            alpha.save()

        version = Version.objects.get_for_object_reference(Dragonfly, alpha.pk).latest(
            "revision__date_created"
        )

        alpha.name = "beta"
        alpha.save()

        sighting.name = "Tokyo"
        sighting.save()

        version_view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["version_restore"]
        )
        response = version_view(request, pk=alpha.pk, version_id=version.pk)

        self.assertEqual(response.status_code, 302)

        alpha.refresh_from_db()
        sighting.refresh_from_db()

        self.assertEqual(alpha.name, "alpha")
        self.assertEqual(sighting.name, "Berlin")

    def test_revert_to_previous_version_requires_change_perm(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        Sighting.objects.create(name="Berlin", dragonfly=alpha)

        request = RequestFactory().post("/", {})
        request.user = user_with_perms([])

        with VersionedDragonflyViewSet().create_revision(request):
            alpha.save()

        version = Version.objects.get_for_object_reference(Dragonfly, alpha.pk).latest(
            "revision__date_created"
        )

        version_view = VersionedDragonflyViewSet()._get_view(
            VersionedDragonflyViewSet().facets["version_restore"]
        )
        with self.assertRaises(PermissionDenied):
            version_view(request, pk=alpha.pk, version_id=version.pk)
