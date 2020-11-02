from beam.actions import DeleteAction
from django.test import TestCase
from django_webtest import WebTest
from test_views import user_with_perms
from testapp.models import Dragonfly, ProtectedSighting, Sighting
from testapp.views import DragonFlyUpdateAction, DragonflyViewSet


class ActionTest(TestCase):
    def test_delete_action(self):
        action = DeleteAction(
            data=None, model=Dragonfly, id="delete-dragonfly", request=None
        )
        Dragonfly.objects.create(name="alpha", age=10)
        Dragonfly.objects.create(name="beta", age=10)
        Dragonfly.objects.create(name="gamma", age=100)
        action.apply(Dragonfly.objects.filter(age__lte=10))
        self.assertEqual(action.get_success_message(), "Deleted 2 dragonflys")
        self.assertEqual(Dragonfly.objects.count(), 1)

    def test_mass_update_action(self):
        Dragonfly.objects.create(name="alpha", age=10)
        Dragonfly.objects.create(name="beta", age=10)
        Dragonfly.objects.create(name="gamma", age=100)

        action = DragonFlyUpdateAction(
            data={"update-age": "100"}, model=Dragonfly, id="update", request=None
        )
        action.apply(Dragonfly.objects.all())

        self.assertEqual(action.get_success_message(), "Updated 2 dragonflys")
        self.assertEqual(Dragonfly.objects.filter(age=100).count(), 3)


class ActionViewTest(WebTest):
    def setUp(self):
        self.alpha = Dragonfly.objects.create(name="alpha", age=12)
        self.omega = Dragonfly.objects.create(name="omega", age=99)

    def test_no_action_selected_does_nothing(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_select[]"] = [self.alpha.pk]
        response = form.submit()
        self.assertContains(response, "alpha")
        self.assertContains(response, "omega")
        self.assertEqual(Dragonfly.objects.count(), 2)

    def test_no_list_items_selected_does_nothing(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        response = form.submit().follow()
        self.assertContains(response, "alpha")
        self.assertContains(response, "omega")
        self.assertEqual(Dragonfly.objects.count(), 2)

    def test_action_with_selection(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        form["_action_select[]"] = [self.alpha.pk]
        response = form.submit().follow()

        self.assertNotContains(response, "alpha")
        self.assertContains(response, "omega")

        self.assertEqual(Dragonfly.objects.count(), 1)

    def test_selection_across_page_boundary(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        form["_action_select_across"] = "all"
        response = form.submit().follow()

        self.assertNotContains(response, "alpha")
        self.assertNotContains(response, "omega")

        self.assertEqual(Dragonfly.objects.count(), 0)

    def test_no_permission_hides_action_from_menu(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.change_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        with self.assertRaises(ValueError):
            form["_action_choice"] = "0-delete"

    def test_no_permission_prevents_action(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.change_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"].force_value("0-delete")
        form["_action_select_across"] = "all"
        response = form.submit()

        self.assertContains(response, "alpha")
        self.assertContains(response, "omega")

        self.assertEqual(Dragonfly.objects.count(), 2)

    def test_invalid_form_shows_error_and_preserves_action_choice(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse(),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.change_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "1-update_selected"
        form["_action_select[]"] = [self.alpha.pk]
        form["1-update_selected-age"] = "not_a_number"

        response = form.submit()

        self.assertContains(response, "Enter a whole number")
        self.assertEqual(
            response.forms["list-action-form"]["_action_choice"].value,
            "1-update_selected",
        )

    def test_filter_interaction(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?filter-name=alpha",
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        form["_action_select_across"] = "all"
        response = form.submit().follow()

        self.assertContains(response, "Deleted 1 dragonflys")

        self.assertFalse(Dragonfly.objects.filter(name="alpha").exists())
        self.assertTrue(Dragonfly.objects.filter(name="omega").exists())

    def test_search_interaction(self):
        list_page = self.app.get(
            DragonflyViewSet().links["list"].reverse() + "?q=omega",
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_dragonfly",]
            ),
        )
        form = list_page.forms["list-action-form"]
        form["_action_choice"] = "0-delete"
        form["_action_select_across"] = "all"
        response = form.submit().follow()

        self.assertContains(response, "Deleted 1 dragonflys")

        self.assertTrue(Dragonfly.objects.filter(name="alpha").exists())
        self.assertFalse(Dragonfly.objects.filter(name="omega").exists())


class InlineActionViewTest(WebTest):
    def setUp(self):
        self.dragonfly = Dragonfly.objects.create(name="alpha", age=12)
        Sighting.objects.create(dragonfly=self.dragonfly, name="regular-sighting-0")
        Sighting.objects.create(dragonfly=self.dragonfly, name="regular-sighting-1")
        ProtectedSighting.objects.create(
            dragonfly=self.dragonfly, name="protected-sighting-0"
        )

    def test_action_shown_only_where_permission(self):
        detail_page = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly),
            user=user_with_perms(
                [
                    "testapp.view_dragonfly",
                    "testapp.delete_sighting",
                    "testapp.delete_protectedsighting",
                ],
                username="user-0",
            ),
        )
        self.assertContains(detail_page, "sighting_set-0-delete")
        self.assertContains(detail_page, "protectedsighting_set-0-delete")

        detail_page_only_sighting = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_sighting",],
                username="user-1",
            ),
        )
        self.assertContains(detail_page_only_sighting, "sighting_set-0-delete")
        self.assertNotContains(
            detail_page_only_sighting, "protectedsighting_set-0-delete"
        )

        detail_page_only_protected_sighting = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_protectedsighting",],
                username="user-2",
            ),
        )
        self.assertContains(
            detail_page_only_protected_sighting, "sighting_set-0-delete"
        )
        self.assertContains(
            detail_page_only_protected_sighting, "protectedsighting_set-0-delete"
        )

    def test_action_with_selection(self):
        detail_page = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_sighting",]
            ),
        )
        form = detail_page.forms["sighting_set-action-form"]
        form["_action_choice"] = "sighting_set-0-delete"
        form["_action_select[]"] = [Sighting.objects.get(name="regular-sighting-0").pk]
        response = form.submit().follow()
        self.assertContains(response, "Deleted 1 sighting")
        self.assertNotContains(response, "regular-sighting-0")
        self.assertContains(response, "regular-sighting-1")

        self.assertEqual(Sighting.objects.count(), 1)

    def test_selection_across_page_boundary(self):
        Sighting.objects.create(dragonfly=self.dragonfly, name="regular-sighting-2")
        Sighting.objects.create(dragonfly=self.dragonfly, name="regular-sighting-3")
        Sighting.objects.create(dragonfly=self.dragonfly, name="regular-sighting-4")
        Sighting.objects.create(dragonfly=self.dragonfly, name="regular-sighting-5")
        detail_page = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly),
            user=user_with_perms(
                ["testapp.view_dragonfly", "testapp.delete_sighting",]
            ),
        )
        form = detail_page.forms["sighting_set-action-form"]
        form["_action_choice"] = "sighting_set-0-delete"
        form["_action_select_across"] = "all"
        response = form.submit().follow()

        self.assertNotContains(response, "regular-sighting-0")
        self.assertNotContains(response, "regular-sighting-1")

        self.assertEqual(Sighting.objects.count(), 0)

    def test_mass_update_form(self):
        detail_page = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly),
            user=user_with_perms(
                [
                    "testapp.view_dragonfly",
                    "testapp.delete_sighting",
                    "testapp.change_sighting",
                ]
            ),
        )
        form = detail_page.forms["sighting_set-action-form"]
        form["_action_choice"] = "sighting_set-1-update_selected"
        form["_action_select_across"] = "all"
        form["sighting_set-1-update_selected-name"] = "a new name"
        response = form.submit().follow()

        self.assertNotContains(response, "regular-sighting-0")
        self.assertEqual(Sighting.objects.filter(name="a new name").count(), 2)
        self.assertEqual(Sighting.objects.exclude(name="a new name").count(), 0)

    def test_no_interaction_with_multiple_inlines(self):
        self.dragonfly.sighting_set.create(name="interaction-test-sighting", pk=999)
        self.dragonfly.protectedsighting_set.create(
            name="interaction-test-protected-sighting", pk=999
        )
        detail_page = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly),
            user=user_with_perms(
                [
                    "testapp.view_dragonfly",
                    "testapp.delete_sighting",
                    "testapp.delete_protectedsighting",
                ]
            ),
        )
        self.assertTrue(Sighting.objects.filter(pk=999).exists())
        self.assertTrue(ProtectedSighting.objects.filter(pk=999).exists())

        sighting_form = detail_page.forms["sighting_set-action-form"]
        sighting_form["_action_choice"] = "sighting_set-0-delete"
        sighting_form["_action_select[]"] = [999]
        sighting_response = sighting_form.submit().follow()
        self.assertContains(sighting_response, "Deleted 1 sighting")

        self.assertFalse(Sighting.objects.filter(pk=999).exists())
        self.assertTrue(ProtectedSighting.objects.filter(pk=999).exists())

        protected_sighting_form = detail_page.forms["protectedsighting_set-action-form"]
        protected_sighting_form["_action_choice"] = "protectedsighting_set-0-delete"
        protected_sighting_form["_action_select[]"] = ["999"]
        protected_sighting_response = protected_sighting_form.submit().follow()
        self.assertContains(protected_sighting_response, "Deleted 1 protected sighting")

        self.assertFalse(Sighting.objects.filter(pk=999).exists())
        self.assertFalse(ProtectedSighting.objects.filter(pk=999).exists())

    def test_filter_interaction(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.delete_sighting"],)

        detail_page = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly), user=user,
        )

        self.assertContains(detail_page, "regular-sighting-0")
        self.assertContains(detail_page, "regular-sighting-1")

        filter_form = detail_page.forms["sighting_set-filter-form"]
        filter_form["sighting_set-filter-name"] = "regular-sighting-0"

        filtered_page = filter_form.submit()

        self.assertContains(filtered_page, "regular-sighting-0")
        self.assertNotContains(filtered_page, "regular-sighting-1")

        action_form = filtered_page.forms["sighting_set-action-form"]
        action_form["_action_choice"] = "sighting_set-0-delete"
        action_form["_action_select_across"] = "all"
        action_response = action_form.submit().follow()

        self.assertContains(action_response, "Deleted 1 sighting")

        self.assertFalse(Sighting.objects.filter(name="regular-sighting-0").exists())
        self.assertTrue(Sighting.objects.filter(name="regular-sighting-1").exists())

    def test_http_response_from_action(self):
        user = user_with_perms(["testapp.view_dragonfly", "testapp.view_sighting"],)

        detail_page = self.app.get(
            DragonflyViewSet().links["detail"].reverse(self.dragonfly), user=user,
        )

        form = detail_page.forms["sighting_set-action-form"]
        form["_action_choice"] = "sighting_set-2-csv_export"
        form["_action_select_across"] = "all"
        response = form.submit()
        self.assertEqual(
            response.content.decode("utf-8"),
            "{},regular-sighting-0\r\n"
            "{},regular-sighting-1\r\n".format(
                Sighting.objects.get(name="regular-sighting-0").pk,
                Sighting.objects.get(name="regular-sighting-1").pk,
            ),
        )
