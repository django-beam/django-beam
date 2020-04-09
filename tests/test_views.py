import pytest
from django.contrib.auth.models import Permission
from pytest import mark
from testapp.models import Dragonfly, Sighting, CascadingSighting, ProtectedSighting
from testapp.views import DragonflyViewSet


def user_with_perms(django_user_model, perms, username="foo", password="bar"):
    user = django_user_model.objects.create_user(username=username, password=password)
    for perm in perms:
        app_label, codename = perm.split(".")
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )
    return user


@pytest.fixture
def client_with_perms(client, django_user_model):
    def get_client_with_perms(*perms):
        user_with_perms(django_user_model, perms, username="foo", password="bar")
        client.login(username="foo", password="bar")
        return client

    return get_client_with_perms


@mark.django_db
def test_list(client_with_perms):
    client = client_with_perms("testapp.view_dragonfly")
    Dragonfly.objects.create(name="alpha", age=12)
    Dragonfly.objects.create(name="omega", age=99)
    response = client.get(DragonflyViewSet().links["list"].reverse())
    assert b"alpha" in response.content
    assert b"omega" in response.content


@mark.django_db
def test_list_search(client_with_perms):
    client = client_with_perms("testapp.view_dragonfly")
    Dragonfly.objects.create(name="alpha", age=12)
    Dragonfly.objects.create(name="omega", age=99)
    response = client.get(DragonflyViewSet().links["list"].reverse() + "?q=alpha")
    assert b"alpha" in response.content
    assert b"omega" not in response.content


@mark.django_db
def test_list_sort(client_with_perms):
    client = client_with_perms("testapp.view_dragonfly")
    Dragonfly.objects.create(name="alpha", age=12)
    Dragonfly.objects.create(name="omega", age=99)

    response = client.get(DragonflyViewSet().links["list"].reverse() + "?o=-name")
    assert response.content.index(b"alpha") > response.content.index(b"omega")

    response = client.get(DragonflyViewSet().links["list"].reverse() + "?o=name")
    assert response.content.index(b"alpha") < response.content.index(b"omega")


@mark.django_db
def test_detail(client_with_perms):
    client = client_with_perms(
        "testapp.view_dragonfly", "testapp.change_dragonfly", "testapp.delete_dragonfly"
    )
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
def test_update(client_with_perms):
    client = client_with_perms("testapp.change_dragonfly")
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    response = client.get(DragonflyViewSet().links["update"].reverse(alpha))
    assert b"alpha" in response.content
    assert "form" in response.context
    assert response.context["form"]["name"].value() == "alpha"


@mark.django_db
def test_delete(client_with_perms):
    client = client_with_perms("testapp.delete_dragonfly")
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    delete_url = DragonflyViewSet().links["delete"].reverse(alpha)
    response = client.get(delete_url)
    assert b"Are you sure you want to delete" in response.content
    assert b"alpha" in response.content

    response = client.post(delete_url)

    assert response.status_code == 302
    assert response["location"] == DragonflyViewSet().links["list"].reverse()

    assert not Dragonfly.objects.filter(name="alpha").exists()


@mark.django_db
def test_delete_shows_related(client_with_perms):
    client = client_with_perms("testapp.delete_dragonfly")
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    CascadingSighting.objects.create(dragonfly=alpha, name="A related sighting")

    delete_url = DragonflyViewSet().links["delete"].reverse(alpha)
    response = client.get(delete_url)

    assert b"The following objects" in response.content
    assert b"sighting" in response.content

    response = client.post(delete_url)

    assert response.status_code == 302
    assert response["location"] == DragonflyViewSet().links["list"].reverse()

    assert not Dragonfly.objects.filter(name="alpha").exists()


@mark.django_db
def test_delete_protected_not_allowed(client_with_perms):
    client = client_with_perms("testapp.delete_dragonfly")
    alpha = Dragonfly.objects.create(name="alpha", age=47)
    ProtectedSighting.objects.create(dragonfly=alpha, name="A related sighting")

    delete_url = DragonflyViewSet().links["delete"].reverse(alpha)
    response = client.get(delete_url)

    assert b"You can't delete" in response.content
    assert b"the following objects depend" in response.content
    assert b"sighting" in response.content

    response = client.post(delete_url)

    assert response.status_code == 403

    assert Dragonfly.objects.filter(name="alpha").exists()


@mark.django_db
def test_create_with_inlines(client_with_perms):
    client = client_with_perms("testapp.add_dragonfly")
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


@mark.django_db
def test_only_popup_param_is_preserved_in_detail_links(client_with_perms):
    client = client_with_perms("testapp.view_dragonfly", "testapp.change_dragonfly")
    instance = Dragonfly.objects.create(name="alpha", age=12)
    response = client.get(
        DragonflyViewSet().links["list"].reverse(),
        data={"_popup": "id_test", "not_preserved": "nope"},
    )

    response_content = response.content.decode("utf-8")

    detail_url = DragonflyViewSet().links["update"].reverse(instance)
    assert detail_url in response_content
    assert detail_url + "?_popup=id_test" in response_content
    assert detail_url + "?_popup=id_test&not_preserved" not in response_content
