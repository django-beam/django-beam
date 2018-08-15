from pytest import mark
from testapp.models import Dragonfly, Sighting
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
    Sighting.objects.create(name="Berlin", dragonfly=alpha)
    Sighting.objects.create(name="Paris", dragonfly=alpha)

    response_content = client.get(f"/dragonfly/{alpha.pk}/").content
    assert b"alpha" in response_content
    assert b"Title of sightings"
    assert b"Berlin" in response_content
    assert b"Paris" in response_content


@mark.django_db
def test_update(client):
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    response = client.get(DragonflyViewSet().links["update"].get_url(alpha))
    assert b"alpha" in response.content
    assert "form" in response.context
    assert response.context["form"]["name"].value() == "alpha"


@mark.django_db
def test_create_with_inlines(client):
    response = client.post(
        "/dragonfly/create/",
        {
            "name": "foobar",
            "age": 81,
            "sighting_set-TOTAL_FORMS": 1,
            "sighting_set-INITIAL_FORMS": 0,
            "sighting_set-MIN_NUM_FORMS": 0,
            "sighting_set-MAX_NUM_FORMS": 999,
            "sighting_set-0-name": "Tokyo",
        },
    )

    dragonfly = Dragonfly.objects.get(name="foobar")

    assert response.status_code == 302
    assert response["location"] == DragonflyViewSet().links["detail"].get_url(dragonfly)

    assert dragonfly.age == 81
    assert dragonfly.sighting_set.get().name == "Tokyo"
