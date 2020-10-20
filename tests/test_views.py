from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django_webtest import WebTest
from testapp.models import CascadingSighting, Dragonfly, ProtectedSighting, Sighting
from testapp.views import DragonflyViewSet


def user_with_perms(perms, username="foo", password="bar", user_model=None):
    user_model = user_model or get_user_model()
    user = user_model.objects.create_user(username=username, password=password)
    for perm in perms:
        app_label, codename = perm.split(".")
        user.user_permissions.add(
            Permission.objects.get(content_type__app_label=app_label, codename=codename)
        )
    return user


class ViewTest(WebTest):
    def test_list(self):
        Dragonfly.objects.create(name="alpha", age=12)
        Dragonfly.objects.create(name="omega", age=99)
        response = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(["testapp.view_dragonfly"]),
        )
        self.assertContains(response, "alpha")
        self.assertContains(response, "omega")

    def test_list_requires_permission(self):
        Dragonfly.objects.create(name="alpha", age=12)
        self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms([]),
            status=403,
        )

    def test_list_search(self):
        Dragonfly.objects.create(name="alpha", age=12)
        Dragonfly.objects.create(name="omega", age=99)
        response = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?q=alpha",
            user=user_with_perms(["testapp.view_dragonfly"]),
        )
        self.assertContains(response, "alpha")
        self.assertNotContains(response, "omega")

    def test_list_sort(self):
        user = user_with_perms(["testapp.view_dragonfly"])

        Dragonfly.objects.create(name="alpha", age=12)
        Dragonfly.objects.create(name="omega", age=99)

        response = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?o=-name", user=user,
        )
        self.assertGreater(
            response.content.index(b"alpha"), response.content.index(b"omega")
        )

        response = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?o=name", user=user
        )
        self.assertLess(
            response.content.index(b"alpha"), response.content.index(b"omega")
        )

    def test_detail(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        Sighting.objects.create(name="Berlin", dragonfly=alpha)
        Sighting.objects.create(name="Paris", dragonfly=alpha)

        links = DragonflyViewSet().links

        response = self.app.get(
            links["detail"].reverse(alpha),
            user=(
                user_with_perms(
                    [
                        "testapp.view_dragonfly",
                        "testapp.change_dragonfly",
                        "testapp.delete_dragonfly",
                    ],
                )
            ),
        )

        self.assertContains(response, "alpha")
        self.assertContains(response, "Title of sightings")

        self.assertContains(response, "Berlin")
        self.assertContains(response, "Paris")

        self.assertContains(response, 'href="{}"'.format(links["list"].reverse(alpha)))
        self.assertContains(
            response, 'href="{}"'.format(links["update"].reverse(alpha))
        )
        self.assertContains(
            response, 'href="{}"'.format(links["delete"].reverse(alpha))
        )

    def test_detail_requires_permission(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        links = DragonflyViewSet().links
        self.app.get(
            links["detail"].reverse(alpha), user=user_with_perms([]), status=403,
        )

    def test_update(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        response = self.app.get(
            DragonflyViewSet().links["update"].reverse(alpha),
            user=user_with_perms(["testapp.change_dragonfly"]),
        )
        self.assertContains(response, "alpha")
        self.assertIn("form", response.context)
        self.assertEqual(response.context["form"]["name"].value(), "alpha")

    def test_update_requires_permission(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        self.app.get(
            DragonflyViewSet().links["update"].reverse(alpha),
            user=user_with_perms([]),
            status=403,
        )

    def test_delete(self):

        alpha = Dragonfly.objects.create(name="alpha", age=47)
        delete_url = DragonflyViewSet().links["delete"].reverse(alpha)
        response = self.app.get(
            delete_url, user=user_with_perms(["testapp.delete_dragonfly"]),
        )

        self.assertContains(response, "Are you sure you want to delete")
        self.assertContains(response, "alpha")

        delete_response = response.form.submit()

        self.assertRedirects(
            delete_response,
            DragonflyViewSet().links["list"].reverse(),
            fetch_redirect_response=False,
        )

        self.assertFalse(Dragonfly.objects.filter(name="alpha").exists())

    def test_delete_shows_related(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        CascadingSighting.objects.create(dragonfly=alpha, name="A related sighting")

        delete_url = DragonflyViewSet().links["delete"].reverse(alpha)
        response = self.app.get(
            delete_url, user=user_with_perms(["testapp.delete_dragonfly"]),
        )
        self.assertContains(response, "The following objects")
        self.assertContains(response, "sighting")

        delete_response = response.form.submit()

        self.assertRedirects(
            delete_response,
            DragonflyViewSet().links["list"].reverse(),
            fetch_redirect_response=False,
        )

        self.assertFalse(Dragonfly.objects.filter(name="alpha").exists())

    def test_delete_protected_not_allowed(self):
        user = user_with_perms(["testapp.delete_dragonfly"])
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        ProtectedSighting.objects.create(dragonfly=alpha, name="A related sighting")

        delete_url = DragonflyViewSet().links["delete"].reverse(alpha)
        response = self.app.get(delete_url, user=user,)
        self.assertContains(response, "You can't delete")
        self.assertContains(response, "the following objects depend")
        self.assertContains(response, "sighting")

        self.app.post(delete_url, user=user, status=403)

        assert Dragonfly.objects.filter(name="alpha").exists()

    def test_delete_requires_permission(self):
        user = user_with_perms([])
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        delete_url = DragonflyViewSet().links["delete"].reverse(alpha)

        self.app.get(delete_url, user=user, status=403)
        self.app.post(delete_url, user=user, status=403)

    def test_create_with_inlines(self):
        user = user_with_perms(["testapp.add_dragonfly"])
        create_page = self.app.get(
            DragonflyViewSet().links["create"].reverse(), user=user
        )

        form = create_page.form

        form["name"] = "foobar"
        form["age"] = "81"
        form["sighting_set-0-name"] = "Tokyo"

        response = form.submit()

        dragonfly = Dragonfly.objects.get(name="foobar")

        self.assertRedirects(
            response,
            DragonflyViewSet().links["detail"].reverse(dragonfly),
            fetch_redirect_response=False,
        )

        self.assertEqual(dragonfly.age, 81)
        self.assertEqual(dragonfly.sighting_set.get().name, "Tokyo")

    def test_only_popup_param_is_preserved_in_detail_links(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.change_dragonfly"])

        instance = Dragonfly.objects.create(name="alpha", age=12)
        response = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user,
            params={"_popup": "id_test", "not_preserved": "nope"},
        )

        detail_url = DragonflyViewSet().links["update"].reverse(instance)

        self.assertContains(response, detail_url)
        self.assertContains(response, detail_url + "?_popup=id_test")
        self.assertNotContains(response, detail_url + "?_popup=id_test&not_preserved")
