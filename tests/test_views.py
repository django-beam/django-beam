from pytest import mark
from testapp.models import Dragonfly
from testapp.views import DragonflyViewSet


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
