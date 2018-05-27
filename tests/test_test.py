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
