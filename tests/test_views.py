from unittest import TestCase, mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils.translation import gettext as _
from django_webtest import WebTest
from testapp.models import (
    CascadingSighting,
    Dragonfly,
    ProtectedSighting,
    Sighting,
    SightingReference,
)
from testapp.views import DragonflyViewSet, ExtraView, SightingViewSet

from beam.views import CreateView, DetailView, ListView, UpdateView


def user_with_perms(perms, username="foo", password="bar", user_model=None):
    user_model = user_model or get_user_model()
    user = user_model.objects.create_user(username=username, password=password)
    for perm in perms:
        app_label, codename = perm.split(".")
        try:
            permission = Permission.objects.get(
                content_type__app_label=app_label, codename=codename
            )
        except Permission.DoesNotExist as e:
            raise Permission.DoesNotExist(
                f"Could not find permission {app_label}.{codename}"
            ) from e
        user.user_permissions.add(permission)
    return user


class TemplateNameTest(TestCase):
    def test_detail_templates(self):
        view = DetailView(
            component=DragonflyViewSet().components["detail"], object=Dragonfly(pk=123)
        )
        self.assertEqual(
            view.get_template_names(),
            ["testapp/dragonfly_detail.html", "beam/detail.html"],
        )

    def test_list_templates(self):
        view = ListView(
            component=DragonflyViewSet().components["list"],
            object_list=Dragonfly.objects.none(),
        )
        self.assertEqual(
            view.get_template_names(), ["testapp/dragonfly_list.html", "beam/list.html"]
        )

    def test_update_templates(self):
        view = UpdateView(
            component=DragonflyViewSet().components["update"], object=Dragonfly(pk=123)
        )
        self.assertEqual(
            view.get_template_names(),
            [
                "testapp/dragonfly_update.html",
                "testapp/dragonfly_form.html",
                "beam/update.html",
            ],
        )

    def test_create_templates(self):
        view = CreateView(
            component=DragonflyViewSet().components["create"], object=Dragonfly(pk=123)
        )
        self.assertEqual(
            view.get_template_names(),
            [
                "testapp/dragonfly_create.html",
                "testapp/dragonfly_form.html",
                "beam/create.html",
            ],
        )

    def test_extra_templates(self):
        view = ExtraView(
            component=DragonflyViewSet().components["extra"], object=Dragonfly(pk=123)
        )
        self.assertEqual(
            view.get_template_names(),
            [
                "testapp/dragonfly_extra.html",
                "testapp/dragonfly_detail.html",
                "beam/detail.html",
            ],
        )

    def test_explicit_template_takes_precedence(self):
        with mock.patch.object(ExtraView, "template_name", "explicit.html"):
            view = ExtraView(
                component=DragonflyViewSet().components["extra"],
                object=Dragonfly(pk=123),
            )
            self.assertEqual(
                view.get_template_names(),
                [
                    "explicit.html",
                    "testapp/dragonfly_extra.html",
                    "beam/detail.html",
                ],
            )


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

    def test_list_pagination_small_numbers(self):
        for i in range(DragonflyViewSet.list_paginate_by * 3):
            Dragonfly.objects.create(name="dragonfly-{:02}".format(i), age=100)

        first_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(["testapp.view_dragonfly"]),
        )
        self.assertContains(first_page, "dragonfly-00")
        self.assertContains(first_page, "dragonfly-01")
        self.assertContains(first_page, "dragonfly-02")
        self.assertContains(first_page, "dragonfly-03")
        self.assertContains(first_page, "dragonfly-04")
        self.assertNotContains(first_page, "dragonfly-05")

        second_page = first_page.click("2")
        self.assertNotContains(second_page, "dragonfly-04")
        self.assertContains(second_page, "dragonfly-05")
        self.assertContains(second_page, "dragonfly-06")
        self.assertContains(second_page, "dragonfly-07")
        self.assertContains(second_page, "dragonfly-08")
        self.assertContains(second_page, "dragonfly-09")
        self.assertNotContains(second_page, "dragonfly-10")

    def test_list_pagination_large_numbers(self):
        for i in range(DragonflyViewSet.list_paginate_by * 10):
            Dragonfly.objects.create(name="dragonfly-{}".format(i), age=100)

        response = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?page=5",
            user=user_with_perms(["testapp.view_dragonfly"]),
        )

        # see beam/partials/pagination.html for a description
        self.assertContains(response, "page=1")
        self.assertContains(response, "page=2")
        self.assertNotContains(response, "page=3")

        self.assertContains(response, "page=4")
        self.assertContains(response, "page=6")

        self.assertNotContains(response, "page=8")
        self.assertContains(response, "page=9")
        self.assertContains(response, "page=10")

    def test_list_pagination_show_all(self):
        for i in range(DragonflyViewSet.list_paginate_by * 2):
            Dragonfly.objects.create(name="dragonfly-{:02}".format(i), age=100)

        first_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(["testapp.view_dragonfly"]),
        )

        show_all_page = first_page.click(_("Show all"))
        self.assertContains(show_all_page, "dragonfly-00")
        self.assertContains(show_all_page, "dragonfly-01")
        self.assertContains(show_all_page, "dragonfly-02")
        self.assertContains(show_all_page, "dragonfly-03")
        self.assertContains(show_all_page, "dragonfly-04")
        self.assertContains(show_all_page, "dragonfly-05")
        self.assertContains(show_all_page, "dragonfly-06")
        self.assertContains(show_all_page, "dragonfly-07")
        self.assertContains(show_all_page, "dragonfly-08")
        self.assertContains(show_all_page, "dragonfly-09")

    def test_list_requires_permission(self):
        Dragonfly.objects.create(name="alpha", age=12)
        self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms([]),
            status=403,
        )

    def test_list_redirects_on_login_required(self):
        Dragonfly.objects.create(name="alpha", age=12)
        response = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=None,
        )
        self.assertRedirects(
            response, "/accounts/login/?next=/dragonfly/", fetch_redirect_response=False
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

    def test_list_filter_with_class(self):
        Dragonfly.objects.create(name="alpha", age=12)
        Dragonfly.objects.create(name="omega", age=99)
        response = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(["testapp.view_dragonfly"]),
        )

        filter_form = response.forms["filter-form"]

        filter_form["filter-max_age"] = "0"
        max_0 = filter_form.submit()
        self.assertNotContains(max_0, "alpha")
        self.assertNotContains(max_0, "omega")

        filter_form["filter-max_age"] = "50"
        max_50 = filter_form.submit()
        self.assertContains(max_50, "alpha")
        self.assertNotContains(max_50, "omega")

        filter_form["filter-max_age"] = "100"
        max_100 = filter_form.submit()
        self.assertContains(max_100, "alpha")
        self.assertContains(max_100, "omega")

    def test_list_filter_with_fields(self):
        alpha = Dragonfly.objects.create(name="alpha", age=12)
        omega = Dragonfly.objects.create(name="omega", age=99)
        Sighting.objects.create(name="Berlin", dragonfly=alpha)
        Sighting.objects.create(name="Tokyo", dragonfly=omega)

        response = self.app.get(
            SightingViewSet().links["list"].reverse(),
            user=user_with_perms(["testapp.view_sighting"]),
        )

        filter_form = response.forms["filter-form"]

        filter_form["filter-name"] = "Tokyo"
        tokyo_response = filter_form.submit()
        self.assertNotContains(tokyo_response, "alpha")
        self.assertContains(tokyo_response, "omega")

        filter_form["filter-name"] = "nothing"
        empty_response = filter_form.submit()
        self.assertNotContains(empty_response, "alpha")
        self.assertNotContains(empty_response, "omega")
        self.assertContains(
            empty_response,
            "Could not find any sightings that match the current filters",
        )

    def test_list_sort(self):
        user = user_with_perms(["testapp.view_dragonfly"])

        Dragonfly.objects.create(name="alpha", age=12)
        Dragonfly.objects.create(name="omega", age=99)

        response = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?o=-name",
            user=user,
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
            links["detail"].reverse(alpha),
            user=user_with_perms([]),
            status=403,
        )

    def test_detail_links_related(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        sighting = Sighting.objects.create(dragonfly=alpha)
        links = SightingViewSet().links
        detail_page = self.app.get(
            links["detail"].reverse(sighting),
            user=user_with_perms(
                [
                    "testapp.view_dragonfly",
                    "testapp.view_sighting",
                ]
            ),
        )
        detail_page.click(
            "alpha", href=DragonflyViewSet().links["detail"].reverse(alpha)
        )

    def test_detail_links_to_related_require_permission(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        sighting = Sighting.objects.create(dragonfly=alpha)
        links = SightingViewSet().links
        detail_page = self.app.get(
            links["detail"].reverse(sighting),
            user=user_with_perms(
                [
                    "testapp.view_sighting",
                ]
            ),
        )
        with self.assertRaises(IndexError):
            detail_page.click(
                "alpha", href=DragonflyViewSet().links["detail"].reverse(alpha)
            )

    def test_update(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        response = self.app.get(
            DragonflyViewSet().links["update"].reverse(alpha),
            user=user_with_perms(
                [
                    "testapp.view_dragonfly",
                    "testapp.change_dragonfly",
                ]
            ),
        )
        self.assertContains(response, "alpha")
        self.assertIn("form", response.context)
        self.assertEqual(response.context["form"]["name"].value(), "alpha")

        form = response.form
        form["name"] = "first"
        update_response = form.submit()

        self.assertRedirects(
            update_response,
            DragonflyViewSet().links["detail"].reverse(obj=alpha),
            fetch_redirect_response=False,
        )

        self.assertContains(
            update_response.follow(),
            "The dragonfly &quot;first&quot; was changed successfully.",
        )

    def test_update_requires_permission(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        self.app.get(
            DragonflyViewSet().links["update"].reverse(alpha),
            user=user_with_perms([]),
            status=403,
        )

    def test_extra_component_requires_permission(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        self.app.get(
            (
                DragonflyViewSet()
                .links["extra"]
                .reverse(alpha, override_kwargs={"special": "param"})
            ),
            user=user_with_perms([]),
            status=403,
        )

    def test_update_and_continue_editing(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        links = DragonflyViewSet().links

        response = self.app.get(
            links["update"].reverse(alpha),
            user=user_with_perms(
                [
                    "testapp.view_dragonfly",
                    "testapp.change_dragonfly",
                ]
            ),
        )
        form = response.form
        update_response = form.submit("submit", value="save_and_continue_editing")

        self.assertRedirects(
            update_response,
            DragonflyViewSet().links["update"].reverse(obj=alpha),
            fetch_redirect_response=False,
        )

    def test_delete(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        delete_url = DragonflyViewSet().links["delete"].reverse(alpha)
        response = self.app.get(
            delete_url,
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly"]
            ),
        )

        self.assertContains(response, "Are you sure you want to delete")
        self.assertContains(response, "alpha")

        delete_response = response.form.submit()

        self.assertRedirects(
            delete_response,
            DragonflyViewSet().links["list"].reverse(),
            fetch_redirect_response=False,
        )
        self.assertContains(
            delete_response.follow(),
            "The dragonfly &quot;alpha&quot; was deleted successfully",
        )
        self.assertFalse(Dragonfly.objects.filter(name="alpha").exists())

    def test_delete_shows_related(self):
        alpha = Dragonfly.objects.create(name="alpha", age=47)
        CascadingSighting.objects.create(dragonfly=alpha, name="A related sighting")

        delete_url = DragonflyViewSet().links["delete"].reverse(alpha)
        response = self.app.get(
            delete_url,
            user=user_with_perms(["testapp.delete_dragonfly"]),
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
        response = self.app.get(
            delete_url,
            user=user,
        )
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
        user = user_with_perms(["testapp.view_dragonfly", "testapp.add_dragonfly"])
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

        self.assertContains(
            response.follow(),
            "The dragonfly &quot;foobar&quot; was added successfully.",
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

    def test_custom_detail_template_for_inline(self):
        user = user_with_perms(["testapp.view_dragonfly"])
        dragonfly = Dragonfly.objects.create(name="alpha", age=12)
        response = self.app.get(
            DragonflyViewSet().links["detail"].reverse(dragonfly),
            user=user,
        )
        self.assertContains(response, "Awesome extra custom template title")

    def test_custom_form_template_for_inline(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.add_dragonfly"])
        response = self.app.get(
            DragonflyViewSet().links["create"].reverse(),
            user=user,
        )
        self.assertContains(response, "Awesome extra custom template title")

    def test_detail_filter_inlines(self):
        user = user_with_perms(["testapp.view_dragonfly"])
        dragonfly = Dragonfly.objects.create(name="alpha", age=12)

        Sighting.objects.create(name="sighting-one", dragonfly=dragonfly)
        Sighting.objects.create(name="sighting-two", dragonfly=dragonfly)

        response = self.app.get(
            DragonflyViewSet().links["detail"].reverse(dragonfly),
            user=user,
        )

        self.assertContains(response, "sighting-one")
        self.assertContains(response, "sighting-two")

        response.form["sighting_set-filter-name"] = "sighting-one"
        filtered = response.form.submit()

        self.assertContains(filtered, "sighting-one")
        self.assertNotContains(filtered, "sighting-two")

    def test_detail_filter_multiple_inlines(self):
        user = user_with_perms(["testapp.view_dragonfly"])
        dragonfly = Dragonfly.objects.create(name="alpha", age=12)

        Sighting.objects.create(name="regular-sighting-one", dragonfly=dragonfly)
        Sighting.objects.create(name="regular-sighting-two", dragonfly=dragonfly)

        ProtectedSighting.objects.create(
            name="protected-sighting-one", dragonfly=dragonfly
        )
        ProtectedSighting.objects.create(
            name="protected-sighting-two", dragonfly=dragonfly
        )

        response = self.app.get(
            DragonflyViewSet().links["detail"].reverse(dragonfly),
            user=user,
        )

        self.assertContains(response, "regular-sighting-one")
        self.assertContains(response, "regular-sighting-two")

        self.assertContains(response, "protected-sighting-one")
        self.assertContains(response, "protected-sighting-two")

        form = response.forms["sighting_set-filter-form"]
        form["sighting_set-filter-name"] = "regular-sighting-one"
        filtered = form.submit()

        self.assertContains(filtered, "regular-sighting-one")
        self.assertNotContains(filtered, "regular-sighting-two")

        self.assertContains(filtered, "protected-sighting-one")
        self.assertContains(filtered, "protected-sighting-two")

    def test_tabular_inline_detail(self):
        user = user_with_perms(["testapp.view_dragonfly"])
        dragonfly = Dragonfly.objects.create(name="alpha", age=12)

        CascadingSighting.objects.create(name="sighting-one", dragonfly=dragonfly)
        CascadingSighting.objects.create(name="sighting-two", dragonfly=dragonfly)

        response = self.app.get(
            DragonflyViewSet().links["detail"].reverse(dragonfly),
            user=user,
        )

        self.assertContains(response, "sighting-one")
        self.assertContains(response, "sighting-two")
        self.assertContains(response, "cascadingsighting_set-table")

    def test_tabular_inline_form(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.change_dragonfly"])
        dragonfly = Dragonfly.objects.create(name="alpha", age=12)

        CascadingSighting.objects.create(name="sighting-one", dragonfly=dragonfly)
        CascadingSighting.objects.create(name="sighting-two", dragonfly=dragonfly)

        response = self.app.get(
            DragonflyViewSet().links["update"].reverse(dragonfly),
            user=user,
        )

        self.assertContains(response, "sighting-one")
        self.assertContains(response, "sighting-two")
        self.assertContains(response, "cascadingsighting_set-table")

    def test_delete_inline(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.change_dragonfly"])

        dragonfly = Dragonfly.objects.create(name="alpha", age=12)
        Sighting.objects.create(name="a-sighting", dragonfly=dragonfly)

        response = self.app.get(
            DragonflyViewSet().links["update"].reverse(dragonfly),
            user=user,
        )

        self.assertContains(response, "a-sighting")

        form = response.form
        form["sighting_set-0-DELETE"] = True
        delete_response = form.submit()

        self.assertRedirects(
            delete_response, DragonflyViewSet().links["detail"].reverse(dragonfly)
        )

        self.assertFalse(dragonfly.sighting_set.exists())

    def test_delete_protected_inline(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.change_dragonfly"])

        dragonfly = Dragonfly.objects.create(name="alpha", age=12)
        sighting = Sighting.objects.create(name="a-sighting", dragonfly=dragonfly)
        SightingReference.objects.create(sighting=sighting)

        response = self.app.get(
            DragonflyViewSet().links["update"].reverse(dragonfly),
            user=user,
        )

        self.assertContains(response, "a-sighting")

        form = response.form
        form["sighting_set-0-DELETE"] = True
        delete_response = form.submit()

        self.assertContains(
            delete_response,
            "would require deleting the following protected related objects",
        )

        self.assertTrue(dragonfly.sighting_set.exists())

    def test_navigation(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.view_sighting"])
        base_page = self.app.get(reverse("base-template"), user=user)
        self.assertContains(base_page, "Testapp")
        self.assertContains(base_page, DragonflyViewSet().links["list"].reverse())
        self.assertContains(base_page, SightingViewSet().links["list"].reverse())

    def test_navigation_respects_permissions(self):
        user = user_with_perms(["testapp.view_sighting"])
        base_page = self.app.get(reverse("base-template"), user=user)
        self.assertNotContains(base_page, DragonflyViewSet().links["list"].reverse())
        self.assertContains(base_page, SightingViewSet().links["list"].reverse())

    def test_navigation_hides_empty_submenus(self):
        user = user_with_perms([])
        base_page = self.app.get(reverse("base-template"), user=user)
        self.maxDiff = None
        self.assertNotContains(base_page, "Testapp")
        self.assertNotContains(base_page, SightingViewSet().links["list"].reverse())
        self.assertNotContains(base_page, DragonflyViewSet().links["list"].reverse())


class InlinePaginationTest(WebTest):
    def test_paginated_detail_inlines(self):
        user = user_with_perms(["testapp.view_dragonfly"])

        dragonfly = Dragonfly.objects.create(name="alpha", age=12)
        for i in range(6):  # SightingInline.paginate_by + 1
            Sighting.objects.create(
                name="sighting-at-{}".format(i), dragonfly=dragonfly
            )

        response = self.app.get(
            DragonflyViewSet().links["detail"].reverse(dragonfly),
            user=user,
        )

        self.assertContains(response, "sighting-at-0")
        self.assertContains(response, "sighting-at-1")
        self.assertContains(response, "sighting-at-2")
        self.assertContains(response, "sighting-at-3")
        self.assertContains(response, "sighting-at-4")
        self.assertNotContains(response, "sighting-at-5")

        next_page = response.click("Next")

        self.assertNotContains(next_page, "sighting-at-0")
        self.assertNotContains(next_page, "sighting-at-1")
        self.assertNotContains(next_page, "sighting-at-2")
        self.assertNotContains(next_page, "sighting-at-3")
        self.assertNotContains(next_page, "sighting-at-4")
        self.assertContains(next_page, "sighting-at-5")

    def test_paginated_update_inlines(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.change_dragonfly"])

        dragonfly = Dragonfly.objects.create(name="alpha", age=12)
        for i in range(6):  # SightingInline.paginate_by + 1
            Sighting.objects.create(
                name="sighting-at-{}".format(i), dragonfly=dragonfly
            )

        response = self.app.get(
            DragonflyViewSet().links["update"].reverse(dragonfly),
            user=user,
        )

        self.assertContains(response, "sighting-at-0")
        self.assertContains(response, "sighting-at-1")
        self.assertContains(response, "sighting-at-2")
        self.assertContains(response, "sighting-at-3")
        self.assertContains(response, "sighting-at-4")
        self.assertNotContains(response, "sighting-at-5")

        form = response.form
        form["sighting_set-0-name"] = "sighting-at-0-changed"
        form["sighting_set-1-DELETE"] = True
        update_response = form.submit()
        self.assertRedirects(
            update_response, DragonflyViewSet().links["detail"].reverse(dragonfly)
        )

        self.assertSetEqual(
            set(dragonfly.sighting_set.values_list("name", flat=True)),
            {
                "sighting-at-0-changed",
                "sighting-at-2",
                "sighting-at-3",
                "sighting-at-4",
                "sighting-at-5",
            },
        )

    def test_dashboard_no_permissions(self):
        user_no_perms = user_with_perms([], username="user-no-perms")

        dashboard_no_perms = self.app.get(
            reverse("dashboard"),
            user=user_no_perms,
        )

        self.assertNotContains(
            dashboard_no_perms, Dragonfly._meta.verbose_name_plural.capitalize()
        )
        self.assertNotContains(dashboard_no_perms, 'href="/dragonfly/"')
        self.assertNotContains(dashboard_no_perms, 'href="/dragonfly/create/"')

        self.assertNotContains(
            dashboard_no_perms, Sighting._meta.verbose_name_plural.capitalize()
        )
        self.assertNotContains(dashboard_no_perms, 'href="/sighting/"')
        self.assertNotContains(dashboard_no_perms, 'href="/sighting/create/"')

    def test_dashboard_one_app_only(self):
        user_dragonfly_only = user_with_perms(
            [
                "testapp.view_dragonfly",
                "testapp.add_dragonfly",
            ],
            username="user-dragonfly",
        )

        dashboard_dragonfly_only = self.app.get(
            reverse("dashboard"),
            user=user_dragonfly_only,
        )

        self.assertContains(
            dashboard_dragonfly_only, Dragonfly._meta.verbose_name_plural.capitalize()
        )
        self.assertContains(dashboard_dragonfly_only, 'href="/dragonfly/"')
        self.assertContains(dashboard_dragonfly_only, 'href="/dragonfly/create/"')

        self.assertNotContains(
            dashboard_dragonfly_only, Sighting._meta.verbose_name_plural.capitalize()
        )
        self.assertNotContains(dashboard_dragonfly_only, 'href="/sighting/"')
        self.assertNotContains(dashboard_dragonfly_only, 'href="/sighting/create/"')

    def test_dashboard_view_all_permissions(self):
        user_view_all = user_with_perms(
            [
                "testapp.view_dragonfly",
                "testapp.view_sighting",
            ],
            username="user-view-all",
        )

        dashboard_view_all = self.app.get(
            reverse("dashboard"),
            user=user_view_all,
        )
        self.assertContains(
            dashboard_view_all, Dragonfly._meta.verbose_name_plural.capitalize()
        )
        self.assertContains(dashboard_view_all, 'href="/dragonfly/"')
        self.assertNotContains(dashboard_view_all, 'href="/dragonfly/create/"')

        self.assertContains(
            dashboard_view_all, Sighting._meta.verbose_name_plural.capitalize()
        )
        self.assertContains(dashboard_view_all, 'href="/sighting/"')
        self.assertNotContains(dashboard_view_all, 'href="/sighting/create/"')
