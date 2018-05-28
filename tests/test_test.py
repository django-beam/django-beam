from beam.templatetags.beam_tags import get_link_url
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
    "testapp_dragonfly_detail": "<str:pk>/",
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
    response = client.get(DragonflyViewSet().links["list"].get_url())
    assert b"alpha" in response.content
    assert b"omega" in response.content


@mark.django_db
def test_detail(client):
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    assert b"alpha" in client.get(f"/dragonfly/{alpha.pk}/").content


@mark.django_db
def test_update(client):
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    response = client.get(f"/dragonfly/{alpha.pk}/update/")
    assert b"alpha" in response.content
    assert "form" in response.context
    assert response.context["form"]["name"].value() == "alpha"


view_types_which_require_object_to_link = {
    "update": "/dragonfly/123/update/",
    "detail": "/dragonfly/123/",
    "delete": "/dragonfly/123/delete/",
}


view_types_which_require_no_object_to_link = {
    "create": "/dragonfly/create/",
    "list": "/dragonfly/",
}


@mark.parametrize("view_type, url", view_types_which_require_no_object_to_link.items())
def test_get_link_urls_that_require_object(view_type, url):
    link = dict(DragonflyViewSet().links)[view_type]
    assert get_link_url(link, None) == url


@mark.parametrize("view_type", view_types_which_require_object_to_link.keys())
def test_get_link_urls_with_missing_object(view_type):
    link = dict(DragonflyViewSet().links)[view_type]
    assert get_link_url(link, None) is None


@mark.parametrize("view_type, url", view_types_which_require_object_to_link.items())
def test_get_link_urls_that_require_object(view_type, url):
    instance = Dragonfly(pk=123)
    link = dict(DragonflyViewSet().links)[view_type]
    assert get_link_url(link, instance) == url


@mark.parametrize("view_type, url", view_types_which_require_no_object_to_link.items())
def test_get_link_urls_that_require_object(view_type, url):
    instance = Dragonfly(pk=123)
    link = dict(DragonflyViewSet().links)[view_type]
    assert get_link_url(link, instance) == url
