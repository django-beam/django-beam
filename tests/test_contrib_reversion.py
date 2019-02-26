from django.contrib.auth import get_user_model
from django.contrib.messages.apps import MessagesConfig
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory
from reversion.models import Version
from pytest import mark
from reversion import is_registered, set_comment

from beam import RelatedInline
from beam.contrib.reversion.viewsets import VersionViewSet
from beam.registry import RegistryType
from testapp.models import Dragonfly, Petaluridae, Sighting


registry: RegistryType = {}


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


VersionedDragonflyViewSet()


def test_versioned_view_set_models_are_registered():
    assert is_registered(Dragonfly)


def test_inlines_of_versioned_view_set_models_are_registered():
    assert is_registered(Sighting)


def test_unrelated_models_are_not_registered():
    assert not is_registered(Petaluridae)


@mark.django_db
def test_using_create_view_creates_a_revision():
    user = get_user_model().objects.create()
    create_view = VersionedDragonflyViewSet()._get_view(
        VersionedDragonflyViewSet().components["create"]
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

    response = create_view(request)

    assert response.status_code == 302

    fly = Dragonfly.objects.get()
    fly_version = Version.objects.get_for_object_reference(Dragonfly, fly.pk).get()

    assert fly_version.object.name == "versionfly"
    assert fly_version.field_dict["name"] == "versionfly"
    assert fly_version.revision.user == user
    assert fly_version.revision.comment == "create"

    sighting_version = Version.objects.get_for_object_reference(
        Sighting, fly.sighting_set.get().pk
    ).get()
    assert sighting_version.field_dict["name"] == "Tokyo"


@mark.django_db
def test_using_update_view_creates_a_revision():
    alpha = Dragonfly.objects.create(name="alpha", age=47)

    user = get_user_model().objects.create()
    update_view = VersionedDragonflyViewSet()._get_view(
        VersionedDragonflyViewSet().components["update"]
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
    response = update_view(request, pk=alpha.pk)

    assert response.status_code == 302

    fly_version = Version.objects.get_for_object_reference(Dragonfly, alpha.pk).latest(
        "revision__created_date"
    )

    assert fly_version.object.name == "beta"
    assert fly_version.field_dict["name"] == "beta"
    assert fly_version.revision.user == user
    assert fly_version.revision.comment == "update"


@mark.django_db
def test_revision_is_visible_in_list():
    alpha = Dragonfly.objects.create(name="alpha", age=47)

    user = get_user_model().objects.create()
    request = RequestFactory().get("/", {})
    request.user = user

    with VersionedDragonflyViewSet().create_revision(request):
        set_comment("number one")
        alpha.save()

    with VersionedDragonflyViewSet().create_revision(request):
        set_comment("number two")
        alpha.save()

    with VersionedDragonflyViewSet().create_revision(request):
        set_comment("number three")
        alpha.save()

    assert Version.objects.get_for_object_reference(Dragonfly, alpha.pk).count() == 3

    view = VersionedDragonflyViewSet()._get_view(
        VersionedDragonflyViewSet().components["version_list"]
    )

    response = view(request, pk=alpha.pk)
    response_content = response.rendered_content

    assert "number one" in response_content
    assert "number two" in response_content
    assert "number three" in response_content


@mark.django_db
def test_show_detail_from_previous_version():
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    sighting = Sighting.objects.create(name="Berlin", dragonfly=alpha)

    user = get_user_model().objects.create()
    request = RequestFactory().get("/", {})
    request.user = user

    with VersionedDragonflyViewSet().create_revision(request):
        alpha.save()

    version = Version.objects.get_for_object_reference(Dragonfly, alpha.pk).latest(
        "revision__created_date"
    )

    alpha.name = "beta"
    alpha.save()

    sighting.name = "Tokyo"
    sighting.save()

    detail_view = VersionedDragonflyViewSet()._get_view(
        VersionedDragonflyViewSet().components["detail"]
    )
    detail_content = detail_view(request, pk=alpha.pk).rendered_content

    assert "beta" in detail_content
    assert "Tokyo" in detail_content

    version_view = VersionedDragonflyViewSet()._get_view(
        VersionedDragonflyViewSet().components["version_detail"]
    )

    version_content = version_view(
        request, pk=alpha.pk, version_id=version.pk
    ).content.decode("utf-8")

    assert "alpha" in version_content
    assert "Berlin" in version_content

    assert "beta" not in version_content
    assert "Tokyo" not in version_content


@mark.django_db
def test_revert_to_previous_version():
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    sighting = Sighting.objects.create(name="Berlin", dragonfly=alpha)

    user = get_user_model().objects.create()
    request = RequestFactory().post("/", {})
    request.user = user
    SessionMiddleware().process_request(request)
    MessageMiddleware().process_request(request)

    with VersionedDragonflyViewSet().create_revision(request):
        alpha.save()

    version = Version.objects.get_for_object_reference(Dragonfly, alpha.pk).latest(
        "revision__created_date"
    )

    alpha.name = "beta"
    alpha.save()

    sighting.name = "Tokyo"
    sighting.save()

    version_view = VersionedDragonflyViewSet()._get_view(
        VersionedDragonflyViewSet().components["version_detail"]
    )
    response = version_view(request, pk=alpha.pk, version_id=version.pk)

    assert response.status_code == 302

    alpha.refresh_from_db()
    sighting.refresh_from_db()

    assert alpha.name == "alpha"
    assert sighting.name == "Berlin"
