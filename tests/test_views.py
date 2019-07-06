from pytest import mark
from testapp.models import Dragonfly, Sighting
from testapp.views import DragonflyViewSet


@mark.django_db
def test_list(client):
    Dragonfly.objects.create(name="alpha", age=12)
    Dragonfly.objects.create(name="omega", age=99)
    response = client.get(DragonflyViewSet().links["list"].reverse())
    assert b"alpha" in response.content
    assert b"omega" in response.content


@mark.django_db
def test_list_search(client):
    Dragonfly.objects.create(name="alpha", age=12)
    Dragonfly.objects.create(name="omega", age=99)
    response = client.get(DragonflyViewSet().links["list"].reverse() + "?q=alpha")
    assert b"alpha" in response.content
    assert b"omega" not in response.content


@mark.django_db
def test_detail(client):
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    Sighting.objects.create(name="Berlin", dragonfly=alpha)
    Sighting.objects.create(name="Paris", dragonfly=alpha)

    links = DragonflyViewSet().links

    response_content = client.get(links["detail"].reverse(alpha)).content.decode(
        "utf-8"
    )

    assert "alpha" in response_content
    assert "Title of sightings"
    assert "Berlin" in response_content
    assert "Paris" in response_content

    assert 'href="{}"'.format(links["list"].reverse(alpha)) in response_content
    assert 'href="{}"'.format(links["update"].reverse(alpha)) in response_content
    assert 'href="{}"'.format(links["delete"].reverse(alpha)) in response_content


@mark.django_db
def test_update(client):
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    response = client.get(DragonflyViewSet().links["update"].reverse(alpha))
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
    assert response["location"] == DragonflyViewSet().links["detail"].reverse(dragonfly)

    assert dragonfly.age == 81
    assert dragonfly.sighting_set.get().name == "Tokyo"
