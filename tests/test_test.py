from beam.templatetags.beam_tags import resolve_links
from pytest import mark
from testapp.models import Dragonfly
from testapp.views import DragonflyViewSet


@mark.django_db
def test_create():
    Dragonfly.objects.create(name="Anna", age="42")
    assert Dragonfly.objects.all().count() == 1


def test_get_urls_produces_urls():
    assert len(DragonflyViewSet().get_urls()) == 5


urls = {
    "testapp_dragonfly_list": "",
    "testapp_dragonfly_detail": "<str:pk>/detail/",
    "testapp_dragonfly_delete": "<str:pk>/delete/",
    "testapp_dragonfly_update": "<str:pk>/update/",
}


@mark.parametrize("url", urls.items())
def test_list_url(url):
    urlpattern = next(filter(lambda p: p.name == url[0], DragonflyViewSet().get_urls()))
    assert str(urlpattern.pattern) == url[1]


@mark.django_db
def test_list(client):
    Dragonfly.objects.create(name="alpha", age=12)
    Dragonfly.objects.create(name="omega", age=99)
    response = client.get("/dragonfly/")
    assert b"alpha" in response.content
    assert b"omega" in response.content


@mark.django_db
def test_detail(client):
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    assert b"alpha" in client.get(f"/dragonfly/{alpha.pk}/detail/").content


@mark.django_db
def test_update(client):
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    response = client.get(f"/dragonfly/{alpha.pk}/update/")
    assert b"alpha" in response.content
    assert "form" in response.context
    assert response.context["form"]["name"].value() == "alpha"


view_types_which_require_object_to_link = {
    "update": "/dragonfly/123/update/",
    "detail": "/dragonfly/123/detail/",
    "delete": "/dragonfly/123/delete/",
}


view_types_which_require_no_object_to_link = {
    "create": "/dragonfly/create/",
    "list": "/dragonfly/",
}


def test_resolve_links_that_require_no_object():
    resolved = resolve_links(DragonflyViewSet().get_links(), None)
    assert resolved == view_types_which_require_no_object_to_link


def test_links_with_missing_object_are_not_resolved():
    resolved = resolve_links(DragonflyViewSet().get_links(), None)
    assert not any(
        view_type in resolved for view_type in view_types_which_require_object_to_link
    )


def test_resolve_links_with_object():
    instance = Dragonfly(pk=123)
    all_links = {}
    all_links.update(view_types_which_require_object_to_link)
    all_links.update(view_types_which_require_no_object_to_link)

    resolved = resolve_links(DragonflyViewSet().get_links(), instance)

    assert resolved == all_links
