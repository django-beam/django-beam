from django.contrib.auth import get_user_model
from django.contrib.messages.apps import MessagesConfig
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory
from pytest import mark

import pytest
from beam import ViewSet
from beam.contrib.autocomplete_light import AutocompleteMixin
from beam.registry import RegistryType
from test_views import user_with_perms
from testapp.models import Dragonfly


registry: RegistryType = {}


class AutocompleteDragonflyViewSet(AutocompleteMixin, ViewSet):
    registry = registry

    model = Dragonfly
    fields = ["name", "age"]
    autocomplete_search_fields = ["name"]


@mark.django_db
def test_autocomplete(django_user_model):
    request = RequestFactory().get("/", {})
    request.user = user_with_perms(django_user_model, ["testapp.view_dragonfly"])

    Dragonfly.objects.create(name="alpha", age=12)
    Dragonfly.objects.create(name="omega", age=99)

    view = AutocompleteDragonflyViewSet()._get_view(
        AutocompleteDragonflyViewSet().components["autocomplete"]
    )

    response = view(request)

    assert b"alpha" in response.content
    assert b"omega" in response.content


@mark.django_db
def test_autocomplete_search(django_user_model):
    request = RequestFactory().get("/", {"q": "Al"})
    request.user = user_with_perms(django_user_model, ["testapp.view_dragonfly"])

    Dragonfly.objects.create(name="alpha", age=12)
    Dragonfly.objects.create(name="omega", age=99)

    view = AutocompleteDragonflyViewSet()._get_view(
        AutocompleteDragonflyViewSet().components["autocomplete"]
    )

    response = view(request)

    assert b"alpha" in response.content
    assert b"omega" not in response.content


@mark.django_db
def test_autocomplete_requires_permission(django_user_model):
    alpha = Dragonfly.objects.create(name="alpha", age=47)

    request = RequestFactory().get("/", {})
    request.user = user_with_perms(django_user_model, [])

    view = AutocompleteDragonflyViewSet()._get_view(
        AutocompleteDragonflyViewSet().components["autocomplete"]
    )

    with pytest.raises(PermissionDenied):
        response = view(request)
